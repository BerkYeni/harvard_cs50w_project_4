from django.contrib.auth.models import AbstractUser
from django.db import models as m
from django.utils import timezone

# Create your models here.
class User(AbstractUser):
    following = m.ManyToManyField("User", related_name="followers")

    def followingAmount(self):
        return self.following.count()

    def followerAmount(self):
        return self.followers.count()

    def followUser(self, user):
        if user == self:
            raise ValueError
        self.following.add(user)


class Post(m.Model):
    id = m.BigAutoField(primary_key=True)
    content = m.CharField(max_length=256)
    poster = m.ForeignKey(User, on_delete=m.CASCADE, related_name="user_posts")
    
    likedBy = m.ManyToManyField(User, blank=True, related_name="likedPosts")
    likes = m.BigIntegerField(default=0)

    date = m.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.poster}: '{self.content}' at {self.date}"

    def likePostBy(self, user):
        if not user in self.likedBy:
            self.likedBy.add(user)
            self.likes += 1
            self.save()
    
    def unlikePostBy(self, user):
        if user in self.likedBy:
            self.likedBy.remove(user)
            self.likes -= 1
            self.save()

    # def save(self, *args, **kwargs):
    #     ''' On save, update timestamps '''
    #     if not self.id:
    #         self.created = timezone.now()
    #     return super(User, self).save(*args, **kwargs)