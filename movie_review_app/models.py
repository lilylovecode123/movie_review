from django.db import models


#账号信息
class Users(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=32, null=False)
    password = models.CharField(max_length=64, null=False)
    name = models.CharField(max_length=20, null=False)
    email = models.EmailField(null=False)
    gender_choices = ((1, "Female"), (2, "Male"),)
    gender = models.SmallIntegerField(choices=gender_choices, null=False)
    age = models.IntegerField(null=False)
    type = models.IntegerField(null=False)
    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True) # add avatar for the user
    class Meta:
        db_table = 'users'

#管理员信息
class Admins(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='id', primary_key=True)
    intro = models.CharField(max_length=125, null=False)
    login_time = models.CharField(max_length=10, null=False)
    class Meta:
        db_table = 'admins'

#电影信息
class Movies(models.Model):
    id = models.AutoField(primary_key=True)
    movie_name = models.CharField(max_length=32,  null=False)
    movie_intro = models.CharField(max_length=256, null=False)
    release_time = models.CharField(max_length=10,db_column='release_time', null=False)
    genre = models.CharField(max_length=20, null=False)
    producer = models.CharField(max_length=10, null=False)
    status = models.BooleanField(default=True, null=False)
    admin = models.ForeignKey(Admins, on_delete=models.CASCADE, db_column='admin_id', default='admin1')

    class Meta:
        db_table = 'movies'


#用户信息
class User(models.Model):
    num_coins = models.IntegerField(null=False)
    num_followers = models.IntegerField(null=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='id', primary_key=True)
    movie = models.ForeignKey(Movies, on_delete=models.CASCADE, db_column='movie_id', null=False)
    class Meta:

        db_table = 'user'

#影评记录
class ReviewLogs(models.Model):
    id = models.AutoField(primary_key=True)
    review_time = models.CharField(max_length=19, null=False)
    comments = models.CharField(max_length= 128, null=False)
    ratings = models.IntegerField(null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=False)
    movie = models.ForeignKey(Movies, on_delete=models.CASCADE, db_column='movie_id', null=False)
    commentedPerson = models.IntegerField( db_column='commented_person', null=False, default=0)
    class Meta:
        db_table = 'review_logs'



class FavoriateLists(models.Model):
    id = models.AutoField(primary_key=True)
    collect_time = models.CharField(max_length=19, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=False)
    class Meta:
        db_table = 'favoriate_lists'


