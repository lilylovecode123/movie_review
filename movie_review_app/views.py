import json
import time
import uuid
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.views import View
from django.db.models import Avg
from django.http import JsonResponse
from movie_review_app import models
from django.shortcuts import get_object_or_404
from .models import *
from datetime import datetime
from movie_review_app import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage

'''
Basic processing class, all other processing views inherit from this class
'''


class BaseView(View):
    '''
    Checks whether the specified parameter exists,
    exists return True, not exists return False.
    '''

    def isExist(param):
        if (param == None) or (param == ''):
            return False
        else:
            return True

    '''
    convert paged query information
    '''

    def parsePage(pageIndex, pageSize, pageTotal, count, data):
        return {'pageIndex': pageIndex, 'pageSize': pageSize, 'pageTotal': pageTotal, 'count': count, 'data': data}

    '''
    successfully query information
    '''

    def success(msg='success'):
        resl = {'code': 0, 'msg': msg}
        return HttpResponse(json.dumps(resl), content_type='application/json; charset=utf-8')

    '''
    successfully query information and gain data
    '''

    def successData(data, msg='success'):
        resl = {'code': 0, 'msg': msg, 'data': data}
        return HttpResponse(json.dumps(resl), content_type='application/json; charset=utf-8')

    '''
    system warning
    '''

    def warning(msg='The operation ids abnormal, please try again'):
        resl = {'code': 1, 'msg': msg}
        return HttpResponse(json.dumps(resl), content_type='application/json; charset=utf-8')

    '''
    system exception information
    '''

    def error(msg='System Error'):
        resl = {'code': 2, 'msg': msg}
        return HttpResponse(json.dumps(resl), content_type='application/json; charset=utf-8')


'''
system processing
'''


class SystemView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'info':
            return SystemView.getSessionInfo(request)
        elif module == 'checkPassword':
            return SystemView.checkPassword(request)
        elif module == 'exit':
            return SystemView.exit(request)
        elif module == 'statistics':
            return SystemView.getStatisticInfo(request)
        else:
            return BaseView.error()

    def post(self, request, module, *args, **kwargs):
        if module == 'info':
            return SystemView.editSessionInfo(request)
        elif module == 'password':
            return SystemView.editSessionPwd(request)
        elif module == 'login':
            return SystemView.login(request)
        else:
            return BaseView.error()

    '''
    gain related statistics info
    '''

    def getStatisticInfo(request):
        loginUser = SystemView.getUserLogin(request.GET.get('token'))
        resl = {}
        # 此处假设管理员管理电影/用户/管理员的所有信息
        if loginUser['type'] == 0:
            resl = {
                'userTotalInfo': models.User.objects.all().count(),
                'adminTotalInfo': models.AdminInfo.objects.all().count(),
                'movieTotalInfo': models.MovieInfo.objects.all().count(),
            }
        else:
            user = models.User.objects.filter(user__id=loginUser['id']).first()
            if (user.movie == 0) and (user.num_coins == 0) and (user.num_followers == 0):
                resl = {
                    'isReview': False,
                    'hasFavoriateLists': False,
                }
            else:
                favoriateList = models.FavoriateLists.objects.filter(user__user__id=loginUser['id'])
                if favoriateList.exists():
                    resl = {
                        'isReview': True,
                        'hasFavoriateLists': True,
                        'movieId': user.movie.id,
                        'favoriateListsId': favoriateList.first().id

                    }
                else:
                    resl = {
                        'isReview': True,
                        'hasFavoriateLists': False,
                        'movieId': user.movie.id
                    }
        return BaseView.successData(resl)

    '''
    user login

    '''

    def login(request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = models.Users.objects.filter(username=username)
        user_id = models.Users.objects.filter(id=cache.get('token')).first()
        if (user.exists()):
            user = user.first()
            if user.password == password:
                token = uuid.uuid4()
                resl = {
                    'token': str(token),
                    'id': user.id,

                }

                cache.set('token', user.id, 60 * 60 * 60 * 3)
                return SystemView.successData(resl)
            else:
                return SystemView.error("User inputs a wrong password.")
        else:
            return SystemView.error("User input a wrong username.")

    '''
    gain login user information
    '''

    def getLoginUser(token):
        print(cache.get('token'))
        # user_id = models.Users.objects.filter(id=cache.get('token')).first()
        user_id = cache.get('token')
        if user_id is None:
            return "there is no user ID in cache"
        user = models.Users.objects.filter(id=user_id).first()
        if user is None:
            return "there is no user ID in DB"
        resl = {
            'id': user.id,
            'username': user.username,
            'password': user.password,
            'name': user.name,
            'email': user.email,
            'gender': user.gender,
            'age': user.age,
            'type': user.type
        }
        # for users
        if user.type == 1:
            related_user = models.User.objects.filter(user__id=user.id).first()
            if related_user is not None and related_user.movie is not None:
                resl['isReview'] == True
            else:
                resl['isReview'] == False
        # for admins
        elif user.type == 2:
            pass
        return resl

    '''
    logout
    '''

    def exit(request):
        token = request.GET.get('token')
        cache.delete(token)
        return BaseView.success()

    '''
    password verification
    '''

    def checkPassword(request):
        originPwd = request.GET.get('originPwd')
        loginUser = SystemView.getUserLogin(request.GET.get('token'))
        if (loginUser['password'] == originPwd):
            return BaseView.success()
        else:
            return BaseView.warning('User inputs wrong original password.')

    '''
    gain login user information
    '''

    def getSessionInfo(request):
        loginUser = SystemView.getLoginUser(request.GET.get('token'))
        return BaseView.successData(loginUser)

    '''
    Edit user login information
    '''

    def editSessionInfo(request):
        user = models.Users.objects.filter(id=request.POST.get('id'))
        if (request.POST.get('username') != user.first().username) & \
                (models.UserInfo.objects.filter(username=request.POST.get('username')).exists()):
            return SystemView.warning("User account already exists.")
        user.update(
            username=request.POST.get('username'),
            name=request.POST.get('name'),
            age=request.POST.get('age'),
            email=request.POST.get('email'),
        )
        return BaseView.success()

    '''
    Edit user login password
    '''

    def editSessionPwd(request):
        loginUser = SystemView.getUserLogin(request.POST.get('token'))

        models.UserInfo.objects. \
            filter(id=loginUser['id']).update(
            password=request.POST.get('newPwd'),
        )
        return BaseView.success()

    '''
    users' information management
    '''


class UsersView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'page':
            return UsersView.getPageInfo(request)
        if module == 'info':
            return UsersView.getInfo(request)
        else:
            return BaseView.error()

    def post(self, request, module, *args, **kwargs):
        if module == 'add':
            return UsersView.addInfo(request)
        elif module == 'edit':
            return UsersView.editInfo(request)
        elif module == 'delete':
            return UsersView.delInfo(request)
        else:
            return BaseView.error()

    '''
    get users' information
    '''

    def getInfo(request):
        # print()

        user = models.User.objects.filter(user__id=request.GET['id']).first()
        # user /= Users.objects.get(id=1)
        # print(user)
        if user.movie != None:
            resl = {
                'id': user.user.id,
                'username': user.user.username,
                'password': user.user.password,
                'gender': user.user.gender,
                'userName': user.user.name,
                'age': user.user.age,
                'email': user.user.email,
                'movieId': user.movie.id,
                'movieName': user.movie.movie_name,
                'isReview': False
            }
            return BaseView.successData(resl)
        else:
            resl = {

                'id': user.id,
                'username': user.username,
                'password': user.password,
                'gender': user.gender,
                'userName': user.name,
                'age': user.age,
                'gender': user.gender,
                'email': user.email,
                'movieId': user.movie.id,
                'movieName': user.movie.name,
                'isReview': True

            }

            return BaseView.successData(resl)

    '''
        Viewing user information by pagination
    '''

    def getPageInfo(request):
        # get query params
        page_index = request.GET.get('page_index', 1)
        page_size = request.GET.get('page_size', 10)
        username = request.GET.get('username')
        password = request.GET.get('password')
        gender = request.GET.get('gender')
        age = request.GET.get('age')
        email = request.GET.get('email')
        # construct query
        query = Q();
        if username:
            query &= Q(username__icontains=username)
        if password:
            query &= Q(password__icontains=password)
        if gender:
            query &= Q(gender__icontains=gender)
        if email:
            query &= Q(email__icontains=email)
        if age:
            query &= Q(age__icontains=age)

        # get paginated data
        user_info = models.Users.objects.filter(query)

        # print(user_info)

        paginator = Paginator(user_info, page_size)
        page_data = paginator.get_page(page_index)

        # format data for response
        data = []
        for user in page_data:
            infoData = models.User.objects.filter(user__id=user.id).first()
            if infoData.movie != None:
                data.append({
                    'id': user.id,
                    'numCoins': infoData.num_coins,
                    'numFollowers': infoData.num_followers,
                    'username': infoData.user.username,
                    'email': user.email,
                    'gender': user.gender,
                    'age': user.age,
                    'movie_name': infoData.movie.movie_name,
                    'release_time': infoData.movie.release_time,
                    'movie_intro': infoData.movie.movie_intro,
                    'movieId': infoData.movie.id,
                    'genre': infoData.movie.genre,
                    'producer': infoData.movie.producer,
                    'isReview': True
                })

            # response_data =

        return BaseView.successData({
            'page_index': page_data.number,
            'page_size': page_size,
            'total_records': paginator.count,
            'total_pages': paginator.num_pages,
            'data': data,
        })

    '''
    add user's information 
    '''

    @transaction.atomic
    def addInfo(request):
        if models.Users.objects.filter(username=request.POST.get('username')).exists():
            return BaseView.warning('This account already exists, please re-enter.')
        user = models.Users.objects.create(
            username=request.POST.get('username'),
            password=request.POST.get('password'),
            email=request.POST.get('email'),
            gender=request.POST.get('gender'),
            age=request.POST.get('age'),
            type=1
        )
        models.User.objects.create(
            user=user,
            num_coins=request.POST.get('num_coins'),
            num_followers=request.POST.get('num_followers'),
            movie_id=request.POST.get('movie_id'),

        )
        return BaseView.success()

    '''
    edit user's information
    '''

    def editInfo(request):
        models.User.objects. \
            filter(user__id=request.POST.get('id')).update(
            num_coins=request.POST.get('num_coins'),
            num_followers=request.POST.get('num_followers')
        )
        return BaseView.success()

    '''
    delete user's information
    '''

    def delInfo(request):
        print(request.POST.get('id'))
        # if (models.Movies.objects.filter(users__user__id=request.POST.get('id')).exists()):
        # return BaseView.warning('There are associated relationships that cannot be deleted')
        models.User.objects.filter(user__id=request.POST.get('id')).delete()
        models.Users.objects.filter(id=request.POST.get('id')).delete()
        return BaseView.success()


'''
Display admin information
'''


class AdminsView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'page':
            return AdminsView.getPageInfo(request)
        else:
            return BaseView.error()

    def post(self, request, module, *args, **kwargs):
        if module == 'add':
            return AdminsView.addInfo(request)
        elif module == 'edit':
            return AdminsView.editInfo(request)
        elif module == 'del':
            return AdminsView.deleteInfo(request)
        else:
            return BaseView.error()

    '''
    Viewing admin information by pagination
    '''

    def getPageInfo(request):
        page_index = request.GET.get('page_index', 1)
        page_size = request.GET.get('page_size', 10)

        adminId = request.GET.get('adminId')
        # adminIntro = request.GET.get('adminIntro')
        # adminLoginTime = request.GET.get('adminLoginTime')

        # query = Q()

        # if BaseView.isExist(adminId):
        #     query &= Q(id__icontains=id)
        # if BaseView.isExist(adminIntro):
        #     query &= Q(intro__icontains=adminIntro)
        # if BaseView.isExist(adminLoginTime):
        #     query &= Q(login_time__icontains=adminLoginTime)
        data = models.Admins.objects.filter(user_id=adminId)

        paginator = Paginator(data, page_size)
        resl = []
        for item in list(paginator.page(page_index)):
            temp = {
                'id': item.user.id,
                'userName': item.user.username,
                'passWord': item.user.password,
                'admin'
                'adminIntro': item.intro,
                'adminLoginTime': item.login_time
            }
            resl.append(temp)
        pageData = BaseView.parsePage(int(page_index), int(page_size),
                                      paginator.page(page_index).paginator.num_pages,
                                      paginator.count, resl)

        return BaseView.successData(pageData)

    '''
    add admins' information
    '''

    @transaction.atomic
    def addInfo(request):
        if models.Users.objects.filter(username=request.POST.get('username')).exists():
            return BaseView.warning('This account already exists, please re-enter.')
        user = models.Users.objects.create(
            username=request.POST.get('username'),
            password=request.POST.get('password'),
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            gender=request.POST.get('gender'),
            age=request.POST.get('age'),
            type=0
        )

        models.Admins.objects.create(
            user=user,
            intro=request.POST.get('intro'),
            login_time=request.POST.get('login_time')
        )
        return BaseView.success()

    '''
    edit admins' information
    '''

    def editInfo(request):
        models.Admins.objects. \
            filter(user__id=request.POST.get('id')).update(
            intro=request.POST.get('intro'),
            login_time=request.POST.get('login_time')
        )
        return BaseView.success()

    '''
    delete admins' information
    '''

    def deleteInfo(request):
        if (models.Movies.objects.filter(admin__user__id=request.POST.get('id')).exists()):
            return BaseView.warning('There are associated relationships that cannot be deleted')
        models.Users.objects.filter(id=request.POST.get('id')).delete()
        return BaseView.success()


'''
movies' information management
'''


class MoviesView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'page':
            return MoviesView.getPageInfo(request)
        elif module == 'info':
            return MoviesView.getInfo(request)
        elif module == 'contain':
            return MoviesView.searchByContainsWords(request)
        elif module == 'search':
            return MoviesView.searchInfo(request)
        elif module == 'newest':
            return MoviesView.newestInfo(request)
        else:
            return BaseView.error()

    def post(self, request, module, *args, **kwargs):
        if module == 'add':
            return MoviesView.addInfo(request)
        elif module == 'edit':
            return MoviesView.editInfo(request)
        elif module == 'del':
            return MoviesView.deleteInfo(request)
        else:
            return BaseView.error()

    '''
    gain movie info
    '''

    def getInfo(request):
        movie_data = models.Movies.objects.filter(id=request.GET.get('id')).first()
        print(movie_data)
        resl = {
            'id': movie_data.id,
            'movie_name': movie_data.movie_name,
            'movie_intro': movie_data.movie_intro,
            'release_time': movie_data.release_time,
            'genre': movie_data.genre,
            'status': movie_data.status,
            'producer': movie_data.producer,
            'adminName': movie_data.admin.user.name,
            'adminGender': movie_data.admin.user.gender,
            'adminAge': movie_data.admin.user.age,
            'adminEmail': movie_data.admin.user.email,
            'adminIntro': movie_data.admin.intro,
            'adminLoginTime': movie_data.admin.login_time
        }
        return BaseView.successData(resl)

    '''
    Viewing movie information by pagination
    '''

    def getPageInfo(request):
        # loginUser = SystemView.getLoginUser(request.GEssT.get('token'))
        loginUser = models.Users.objects.filter(id=cache.get('token')).first()

        pageIndex = request.GET.get('pageIndex', 1)
        pageSize = request.GET.get('pageSize', 10)
        adminName = request.GET.get('adminName')
        moviesName = request.GET.get('moviesName')
        query = Q()
        if loginUser is not None and loginUser.type == 0:
            query = query & Q(admin__user__id=loginUser.id)
        if BaseView.isExist(adminName):
            query = query & Q(admin__user__name__contains=adminName)
        if BaseView.isExist(moviesName):
            query = query & Q(name__contains=moviesName)
        data = models.Movies.objects.filter(query).order_by('-release_time')
        paginator = Paginator(data, pageSize)
        resl = []
        for item in list(paginator.page(pageIndex)):
            temp = {
                'id': item.id,
                'movie_name': item.movie_name,
                'movie_intro': item.movie_intro,
                'release_time': item.release_time,
                'genre': item.genre,
                'producer': item.producer,
                'status': item.status,
                'adminName': item.admin.user.name,
                'adminGender': item.admin.user.gender,
                'adminEmail': item.admin.user.email,
                'adminAge': item.admin.user.age,
                'adminIntro': item.admin.intro,
                'adminLoginTime': item.admin.login_time
            }
            resl.append(temp)
        pageData = BaseView.parsePage(int(pageIndex), int(pageSize),
                                      paginator.page(pageIndex).paginator.num_pages,
                                      paginator.count, resl)

        return BaseView.successData(pageData)

    '''
    search movies' info according to genre
    '''
    def searchByContainsWords(request):
        contain = request.GET.get('contain')
        movies = models.Movies.objects.filter(movie_name__icontains=contain)
        data = []
        for movie in movies:
            temp = {
                'id': movie.id,
                'movie_name': movie.movie_name,
                'movie_intro': movie.movie_intro,
                'release_time': movie.release_time,
                'genre': movie.genre,
                'producer': movie.producer,
                'status': movie.status,
                'adminName': movie.admin.user.name,
                'adminGender': movie.admin.user.gender,
                'adminEmail': movie.admin.user.email,
                'adminAge': movie.admin.user.age,
                'adminIntro': movie.admin.intro,
                'adminLoginTime': movie.admin.login_time
            }
            data.append(temp)
        return BaseView.successData(data)

    def searchInfo(request):
        genre = request.GET.get('genre')
        movies = models.Movies.objects.filter(genre=genre)
        resl = []
        for movie in movies:
            temp = {
                'id': movie.id,
                'movie_name': movie.movie_name,
                'movie_intro': movie.movie_intro,
                'release_time': movie.release_time,
                'genre': movie.genre,
                'producer': movie.producer,
                'status': movie.status,
                'adminName': movie.admin.user.name,
                'adminGender': movie.admin.user.gender,
                'adminEmail': movie.admin.user.email,
                'adminAge': movie.admin.user.age,
                'adminIntro': movie.admin.intro,
                'adminLoginTime': movie.admin.login_time
            }
            resl.append(temp)
        return BaseView.successData(resl)

    '''
        get the newest movies' info 
    '''
    def newestInfo(request):
        params = request.GET.get('params')
        if params == 'release_time':
            movies = models.Movies.objects.all().order_by('-release_time')
        elif params == 'ratings':
            movies = models.Movies.objects.annotate(avg_rating=Avg('reviewlogs__ratings')).order_by('-avg_rating')
        else:
            return BaseView.error("Invalid params.")
        resl = []
        for movie in movies:
            temp = {
                'id': movie.id,
                'movie_name': movie.movie_name,
                'movie_intro': movie.movie_intro,
                'release_time': movie.release_time,
                'genre': movie.genre,
                'producer': movie.producer,
                'status': movie.status,
                'adminName': movie.admin.user.name,
                'adminGender': movie.admin.user.gender,
                'adminEmail': movie.admin.user.email,
                'adminAge': movie.admin.user.age,
                'adminIntro': movie.admin.intro,
                'adminLoginTime': movie.admin.login_time
            }
            if params == 'avg_rating':
                temp['avg_rating'] = movie.avg_rating
            resl.append(temp)
        return BaseView.successData(resl)

    '''
    add Movies' info
    '''

    def addInfo(request):
        models.Movies.objects.create(
            admin_id=cache.get('token'),
            movie_name=request.POST.get('movie_name'),
            movie_intro=request.POST.get('movie_intro'),
            release_time=time.strftime("%Y-%m-%d", time.localtime()),
            genre=request.POST.get('genre'),
            status=0,
            producer=request.POST.get('producer'),
        )
        return BaseView.success()

    def editInfo(request):
        models.Movies.objects. \
            filter(id=request.POST.get('id')).update(
            movie_name=request.POST.get('movie_name'),
            movie_intro=request.POST.get('movie_intro'),
            release_time=request.POST.get('release_time'),
            genre=request.POST.get('genre'),
            producer=request.POST.get('producer')
        )
        return BaseView.success()

    def deleteInfo(request):
        if (models.Movies.objects.filter(admin__user__id=cache.get('token')).exists()):
            return BaseView.warning('There are associated relationships that cannot be deleted')
        models.Movies.objects.filter(id=request.POST.get('id')).delete()
        return BaseView.success()


class ReviewLogsView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'page':
            return ReviewLogsView.getPageInfo(request)
        else:
            return BaseView.error()

    def post(self, request, module, *args, **kwargs):
        if module == 'add':
            return ReviewLogsView.addInfo(request)
        elif module == 'edit':
            return ReviewLogsView.editInfo(request)
        elif module == 'confirm':
            return ReviewLogsView.confirmInfo(request)
        elif module == 'del':
            return ReviewLogsView.deleteInfo(request)
        else:
            return BaseView.error()

    '''
    View movie review records by pageination
    '''

    # def getPageInfo(request):
    #     loginUser = SystemView.getLoginUser(request.GET.get('token'))
    #     loginUser = models.Users.objects.filter(id=cache.get('token')).first()
    #     print(cache.get('token'))
    #     pageIndex = request.GET.get('pageIndex', 1)
    #     pageSize = request.GET.get('pageSize', 10)
    #     username = request.GET.get('username')
    #     movie_name = request.GET.get('movie_name')
    #     query = Q()
    #     if loginUser is not None and loginUser.type == 0:
    #         query = query & Q(movie__admin__user__id=loginUser.id)
    #     if loginUser is not None and loginUser.type == 1:
    #         query = query & Q(user__user__id=loginUser.id)
    #     if BaseView.isExist(username):
    #         query = query & Q(user__user__name__contains=username)
    #     if BaseView.isExist(movie_name):
    #         movie = models.Movies.objects.filter(movie_name=movie_name).first()
    #         query = query & Q(movie__id__contains=movie.id)
    #         # print(movie.id)
    #         # query = query & Q(movie__movie__name=movie_name)
    #     # print(query)
    #     data = models.ReviewLogs.objects.filter(query).order_by("-review_time")
    #     paginator = Paginator(data, pageSize)
    #     resl = []
    #     for item in list(paginator.page(pageIndex)):
    #         temp = {
    #             'id': item.id,
    #             'num_coins': item.user.num_coins,
    #             'num_followers': item.user.num_followers,
    #             'movieId': item.user.movie.id,
    #             'movieName': item.user.movie.movie_name,
    #             'adminName': item.user.user.name,
    #             'adminIntro': item.movie.admin.intro,
    #             'adminLoginTime': item.movie.admin.login_time,
    #             'reviewTime': item.review_time,
    #             'comments': item.comments,
    #             'ratings': item.ratings
    #         }
    #         resl.append(temp)
    #     pageData = BaseView.parsePage(int(pageIndex), int(pageSize),
    #                                   paginator.page(pageIndex).paginator.num_pages,
    #                                   paginator.count, resl)
    #
    #     return BaseView.successData(pageData)
    def getPageInfo(request):
        id = request.GET.get('id')
        if BaseView.isExist(id):
            movie = models.Movies.objects.filter(id=id).first()
            if movie is not None:
                data = models.ReviewLogs.objects.filter(movie_id=movie.id).order_by('-review_time')
                avg_ratings = data.aggregate(Avg('ratings'))['ratings__avg']
            else:
                data = []
                avg_ratings = None
        else:
            data = models.ReviewLogs.objects.none()
            avg_ratings = None
        pageIndex = request.GET.get('pageIndex', 1)
        pageSize = request.GET.get('pageSize', 10)
        paginator = Paginator(data, pageSize)
        resl = []
        for item in list(paginator.page(pageIndex)):
            temp = {
                'reviewTime': item.review_time,
                'comments': item.comments,
                'ratings': item.ratings,
                'username': item.user.user.username
            }
            resl.append(temp)
        pageData = BaseView.parsePage(int(pageIndex), int(pageSize),
                                      paginator.page(pageIndex).paginator.num_pages,
                                      paginator.count, resl)
        response_data = {
            'pageData': pageData,
            'avgRatings': avg_ratings
        }
        return BaseView.successData(response_data)

    '''
    add review logs
    '''

    @transaction.atomic
    def addInfo(request):
        loginUser = cache.get('token')
        if not loginUser:
            return BaseView.error('invalid token')
        movie = models.Movies.objects.filter(id=request.POST.get('movie_id')).first()
        user = models.User.objects.filter(user_id=loginUser).first()
        if not movie or not user:
            return BaseView.error('invalid ID or user ID')
        models.ReviewLogs.objects.create(
            user=user,
            comments=request.POST.get('comments'),
            ratings=request.POST.get('ratings'),
            movie=movie,
            commentedPerson=1,
            review_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        )
        return BaseView.success()

    def editInfo(request):
        models.ReviewLogs.objects. \
            filter(id=request.POST.get('id')).update(
            comments=request.POST.get('comments'),
            ratings=request.POST.get('ratings')
        )
        return BaseView.success()


class AvatarView(BaseView):
    # def post(self, request, *args, **kwargs):
    def post(self, request, module, *args, **kwargs):
        if module == 'avatar':
            return AvatarView.upload(request)
        elif module == 'movie':
            return AvatarView.movie(request)
        else:
            return BaseView.error()

    def upload(request):
        print(request.FILES.get('avatar'))
        avatar = request.FILES.get('avatar')
        fss = FileSystemStorage()
        file = fss.save(avatar.name, avatar)
        print(file)
        file_url = fss.url(file)
        print(file_url)
        # save_path = '%s/avatar/%s'%(settings.MEDIA_ROOT,avatar.name)
        # with open (save_path,'wb') as f:
        #     for content in avatar.chunks:
        #         f.write(content)
        # print(avatar.name)
        return BaseView.successData({'file_url': file_url})

    def movie(request):
        print(request.FILES.get('avatar'))
        movie = request.FILES.get('movie')
        fss = FileSystemStorage()
        file = fss.save(movie.name, movie)
        print(file)
        file_url = fss.url(file)
        print(file_url)
        # save_path = '%s/avatar/%s'%(settings.MEDIA_ROOT,avatar.name)
        # with open (save_path,'wb') as f:
        #     for content in avatar.chunks:
        #         f.write(content)
        # print(avatar.name)
        return BaseView.successData({'file_url': file_url})
        # file_serializer = FileSerializer(data = request.data)
