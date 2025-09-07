from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionViewSet, StartQuizRoundView, ActiveQuizRoundView, GetQuestionView, SubmitAnswerView, QuizLeaderboardView, QuestionPoolViewSet, AllQuizRoundsView

router = DefaultRouter()
router.register(r'questions', QuestionViewSet)

question_pool_router = DefaultRouter()
question_pool_router.register(r'question-pools', QuestionPoolViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(question_pool_router.urls)),
    path('start-round/<uuid:tournament_id>', StartQuizRoundView.as_view(), name='start-quiz-round'),
    path('active-round/', ActiveQuizRoundView.as_view(), name='active-quiz-round'),
    path('get-question/', GetQuestionView.as_view(), name='get-question'),
    path('submit-answer/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('leaderboard/<uuid:quiz_round_id>/', QuizLeaderboardView.as_view(), name='quiz-leaderboard'),
    path('rounds', AllQuizRoundsView.as_view(), name='all-quiz-rounds')
]
