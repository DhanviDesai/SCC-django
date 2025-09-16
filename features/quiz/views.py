from rest_framework import viewsets
from .models import Question
from .serializers import QuestionSerializer, QuizRoundSerializer, UserQuizAttemptSerializer, QuizResultSerializer, QuestionPoolSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from features.utils.permissions import IsAdminRole
from features.utils.authentication import FirebaseAuthentication
from features.tournament.models import Tournament
from features.users.models import User
from django.db.models import Q
from .models import QuizRound, UserQuizAttempt, QuizResult, QuestionPool
from datetime import datetime, timedelta, timezone
import random
from features.utils.response_wrapper import error_response, success_response

class QuestionViewSet(viewsets.ModelViewSet):
    authentication_classes = [FirebaseAuthentication]
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAdminRole]
        return super().get_permissions()
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

# We will start the quiz round. Only one active round at a time. The quiz tournament would be request_param
# This would be called by admin, so he would know the tournament id and when to start
class StartQuizRoundView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request, tournament_id=None):
        if tournament_id is None:
            return error_response(message="Tournament ID cannot be null")
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        
        if 'quiz' not in tournament.type.name.lower():
            return error_response(message="Tournament is not of type Quiz", status=status.HTTP_400_BAD_REQUEST)
        
        start_datetime = request.data.get('start_time')
        end_datetime = request.data.get('end_time')
        if start_datetime and end_datetime:
            try:
                start_time = datetime.fromisoformat(start_datetime)
                end_time = datetime.fromisoformat(end_datetime)
                if start_time >= end_time:
                    return error_response(message="End time must be after start time", status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return error_response(message="Invalid date format. Use ISO 8601 format.", status=status.HTTP_400_BAD_REQUEST)
        else:
            return error_response(message="Start time and end time are required", status=status.HTTP_400_BAD_REQUEST)
        
        duration = request.data.get('duration')
        if duration is None:
            return error_response(message="Duration is required", status=status.HTTP_400_BAD_REQUEST)
        try:
            duration = int(duration)
            if duration <= 0:
                return error_response(message="Duration must be a positive integer", status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return error_response(message="Duration must be an integer", status=status.HTTP_400_BAD_REQUEST)
        
        question_pool = request.data.get('question_pool')
        if question_pool is None:
            return error_response(message="Question pool is required", status=status.HTTP_400_BAD_REQUEST)
        try:
            question_pool = QuestionPool.objects.get(id=question_pool)
        except QuestionPool.DoesNotExist:
            return error_response(message="Question pool not found", status=status.HTTP_404_NOT_FOUND)
        
        quiz_round = QuizRound.objects.create(
            tournament=tournament,
            start_time=start_time,
            end_time=end_time,
            question_pool=question_pool,
            duration=duration
        )
        
        # Have to notify the registrants that a new quiz round was added

        return success_response(data={'message': 'Quiz round started successfully.', 'quiz_round_id': quiz_round.id}, status=status.HTTP_201_CREATED)

# This view will return the active quiz round of any quiz tournament
class ActiveQuizRoundView(APIView):
    authentication_classes = [FirebaseAuthentication]

    def get(self, request):
        user_id = request.auth.get('user_id')
        user = User.objects.get(firebase_uid=user_id)
        tournaments = user.tournament_user.filter(type__name__icontains='quiz')
        if not tournaments.exists():
            return error_response(message='User is not registered to any quiz tournaments.', status=status.HTTP_404_NOT_FOUND)
        # Check for active quiz rounds in these tournaments where the user has not attempted
        # Get all the QuizRound objects where the tournament is in tournaments and the QuizRound is not there for the user in UserQuizAttempt

        active_round = QuizRound.objects.filter(
            tournament__in=tournaments,
        ).exclude(
            id__in=UserQuizAttempt.objects.filter(user=user).values_list('quiz_round_id', flat=True)
        )
        serializer = QuizRoundSerializer(active_round, many=True)
        return success_response(data=serializer.data, status=status.HTTP_200_OK)

# This would return a list of 5 questions always
class GetQuestionView(APIView):
    authentication_classes = [FirebaseAuthentication]

    def post(self, request):
        quiz_round_id = request.data.get('quiz_round_id')
        if quiz_round_id is None:
            return error_response(message="Quiz round id cannot be null")
        
        try:
            quiz_round = QuizRound.objects.get(id=quiz_round_id)
        except QuizRound.DoesNotExist:
            return error_response(message="Quiz round not found", status=status.HTTP_404_NOT_FOUND)

        user = User.objects.get(firebase_uid=request.auth.get('user_id'))
        answered_questions_ids = UserQuizAttempt.objects.filter(user=user, quiz_round=quiz_round).values_list('question_id', flat=True)
        unanswered_questions = request.data.get('unanswered_questions', [])
        answered_questions_ids = list(answered_questions_ids) + unanswered_questions
        remaining_questions = Question.objects.filter(pool=quiz_round.question_pool).exclude(id__in=answered_questions_ids)
        # Select 5 random questions from remaining questions
        if not remaining_questions.exists():
            return error_response(message="No more questions available", status=status.HTTP_404_NOT_FOUND)
        selected_questions = random.sample(list(remaining_questions), min(5, remaining_questions.count()))
        serializer = QuestionSerializer(selected_questions, many=True)
        return success_response(data=serializer.data, status=status.HTTP_200_OK)

class SubmitAnswerView(APIView):
    authentication_classes = [FirebaseAuthentication]
    serializer_class = UserQuizAttemptSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                question = serializer.validated_data['question']
                selected_answer = serializer.validated_data['selected_answer']
                quiz_round = serializer.validated_data['quiz_round']
                user = User.objects.get(firebase_uid=request.auth.get('user_id'))

                if UserQuizAttempt.objects.filter(user=user, quiz_round=quiz_round, question=question).exists():
                    return Response({'error': 'You have already answered this question.'}, status=status.HTTP_400_BAD_REQUEST)

                is_correct = (question.correct_answer == selected_answer)
                score = 1 if is_correct else 0

                UserQuizAttempt.objects.create(
                    user=user,
                    quiz_round=quiz_round,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=is_correct,
                    score=score
                )

                quiz_result, created = QuizResult.objects.get_or_create(
                    user=user, 
                    quiz_round=quiz_round, 
                    defaults={'score': 0}
                )
                quiz_result.score += score
                quiz_result.save()

                return success_response(data={'correct': is_correct, 'score': quiz_result.score}, status=status.HTTP_200_OK)

            except QuizRound.DoesNotExist:
                return error_response(message='No active quiz round found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return error_response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuestionPoolViewSet(viewsets.ModelViewSet):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    queryset = QuestionPool.objects.all()
    serializer_class = QuestionPoolSerializer

class QuizLeaderboardView(APIView):
    authentication_classes = [FirebaseAuthentication]

    def get(self, request, quiz_round_id, *args, **kwargs):
        try:
            results = QuizResult.objects.filter(quiz_round_id=quiz_round_id).order_by('-score')
            serializer = QuizResultSerializer(results, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except QuizResult.DoesNotExist:
            return Response({'message': 'Results not found for this round.'}, status=status.HTTP_404_NOT_FOUND)

class AllQuizRoundsView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        quiz_rounds = QuizRound.objects.all().order_by('-start_time')
        serializer = QuizRoundSerializer(quiz_rounds, many=True)
        return success_response(data=serializer.data, status=status.HTTP_200_OK)