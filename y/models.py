from django.contrib.auth.models import AbstractUser
from django.db import models as m
from django.utils import timezone

# Create your models here.
class User(AbstractUser):
    pass

class Post(m.Model):
    id = m.BigAutoField(primary_key=True)
    content = m.CharField(max_length=256)
    poster = m.ForeignKey(User, on_delete=m.CASCADE, related_name="user_posts")
    
    liked_by = m.ManyToManyField(User, blank=True, related_name="likedPosts")

    date = m.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.poster}: '{self.content}' at {self.date}"

    def likeAmount(self):
        return self.liked_by.count()

    # def save(self, *args, **kwargs):
    #     ''' On save, update timestamps '''
    #     if not self.id:
    #         self.created = timezone.now()
    #     return super(User, self).save(*args, **kwargs)