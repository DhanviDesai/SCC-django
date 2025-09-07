from django.db import models
import uuid
from features.tournament.models import Tournament
from features.users.models import User

class QuestionPool(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=255)
    pool = models.ForeignKey(QuestionPool, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.text

class QuizRound(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes", default=2)
    is_active = models.BooleanField(default=False)
    question_pool = models.ForeignKey(QuestionPool, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.tournament.name} - {self.start_time}"

class UserQuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_round = models.ForeignKey(QuizRound, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.name} - {self.question.text}"

class QuizResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_round = models.ForeignKey(QuizRound, on_delete=models.CASCADE)
    score = models.IntegerField()
    completed_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - Score: {self.score}"