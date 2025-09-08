from rest_framework import serializers
from .models import Question, QuizRound, UserQuizAttempt, QuizResult, QuestionPool
from features.users.models import User

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

class QuizRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizRound
        fields = '__all__'

class UserQuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuizAttempt
        fields = ['question', 'selected_answer', 'quiz_round']

class QuizResultSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = QuizResult
        fields = ['user_name', 'score', 'completed_time']

class QuestionPoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionPool
        fields = '__all__'
