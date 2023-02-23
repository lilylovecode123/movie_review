import json
import time
import uuid
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.views import View
from django.http import JsonResponse


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
        return {'pageIndex':pageIndex, 'pageSize':pageSize, 'pageTotal':pageTotal, 'count':count, 'data':data}
    '''
    successfully query information
    '''
    def success(msg='success'):
        resl = {'code':0, 'msg':msg}
        return HttpResponse(json.dumps(resl), content_type='application/json; charset=utf-8')
    '''
    successfully query information and gain data
    '''
    def successData(data, msg='success'):
        resl={'code':0, 'msg':msg, 'data':data}
        return HttpResponse(json.dumps(resl), content_type='application/json; charset=utf-8')
    '''
    system warning
    '''
    def warning(msg='The operation ids abnormal, please try again'):
        resl = {'code':1, 'msg':msg}
        return HttpResponse(json.dumps(resl), content_type='application/json; charset=utf-8')
    '''
    system exception information
    '''
    def error(msg='System Error'):
        resl = {'code':2, 'msg':msg}
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
        #此处假设管理员管理电影/用户/管理员的所有信息
        if loginUser['type'] == 0:
            resl = {
                'userTotalInfo': models.User.objects.all().count(),
                'adminTotalInfo': models.AdminInfo.objects.all().count(),
                'movieTotalInfo': models.MovieInfo.objects.all().count(),
            }
        else:
            user = models.User.objects.filter(user__id =loginUser['id']).first()
            if (user.movie == 0 ) and (user.num_coins == 0) and (user.num_followers == 0):
                resl = {
                    'isReview': False,
                    'hasFavoriateLists': False,
                }
            else:
                favoriateList = models.FavoriateLists.objects.filter(user__user__id = loginUser['id'])
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
        user = models.Users.objects.filter(username=username).first()
        if (user.exists()):
            user = user.first()
            if user.password == password:
                token = uuid.uuid4()
                resl = {
                    'token':str(token)
                }

                cache.set(token, user.id, 60 * 60 * 60 * 3)
                return SystemView.successData(resl)
            else:
                return SystemView.error("User inputs a wrong password.")
        else:
            return SystemView.error("User input a wrong username.")
    '''
    gain user login information
    '''
    def getUserLogin(token):
        user = models.Users.objects.filter(id=cache.get(token)).first()
        #针对用户
        if user.id != 0:
            user = models.UserInfo.objects.filter(user__id = user.id).first()
            if user.movie != None:
                resl = {
                    'id': user.id,
                    'username': user.username,
                    'password': user.password,
                    'name':user.name,
                    'email': user.email,
                    'gender': user.gender,
                    'age': user.age,
                    'type':user.type,
                    'isReview': True
                }
                return resl
        #针对admin
        else:
            resl = {
                'id': user.id,
                'username': user.username,
                'password': user.password,
                'name': user.name,
                'email': user.email,
                'gender': user.gender,
                'age': user.age,
                'type': user.type,
            }
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
        loginUser = SystemView.getUserLogin(request.GET.get('token'))
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
            username = request.POST.get('username'),
            name = request.POST.get('name'),
            age = request.POST.get('age'),
            email = request.POST.get('email'),
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
            return UserView.getInfo(request)
        else:
            return BaseView.error()

    def post(self,request, module, *args, **kwargs):
        if module == 'add':
            return UsersView.addInfo(request)
        elif module == 'edit':
            return UsersView.editInfo(request)
        # elif module == 'confirm':
        #     return UsersView.confirmInfo(request)
        elif module == 'delete':
            return UsersView.delInfo(request)
        else:
            return BaseView.error()
    '''
    get users' information
    '''

    def getInfo(request):
        user = models.Users.objects.filter(user__id=request.POST.get('id')).first()
        if user.movie != None:
            resl = {
                'id': user.id,
                'username': user.username,
                'password': user.password,
                'gender':user.gender,
                'userName': user.name,
                'age': user.age,
                'gender': user.gender,
                'email': user.email,
                'movieId':user.movie.id,
                'movieName':user.movie.name,
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

    def getInfo(request):
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
        user_info = UserInfo.objects.filter(query)
        paginator = Paginator(user_info, page_size)
        page_data = paginator.get_page(page_index)

        # format data for response
        data = []
        for user in page_data:
            data.append({
                'id': users.id,
                'numCoins':user.num_coins,
                'numFollowers':user.num_followers,
                'username': users.username,
                'email': users.email,
                'gender': users.gender,
                'age': users.age,
                'movie_name': user.movies.movie_name,
                'release_time': user.movies.release_time,
                'movie_intro': user.movies.movie_intro,
                'movieId':user.movies.id,
                'genre': user.movies.genre,
                'producer': user.movies.producer,
                'isReview': True
            })

        response_data = {
            'page_index': page_data.number,
            'page_size': page_size,
            'total_records': paginator.count,
            'total_pages': paginator.num_pages,
            'data': data,
        }

        return JsonResponse(response_data)


    '''
    add user's information 
    '''
    @transaction.atomic
    def addInfo(request):
        if models.Users.objects.filter(username=request.POST.get('username')).exists():
            return BaseView.warning('This account already exists, please re-enter.')
        user = models.UserInfo.objects.create(
            username=request.POST.get('username'),
            password=request.POST.get('password'),
            email=request.POST.get('email'),
            gender=request.POST.get('gender'),
            age=request.POST.get('age'),
            type=1
        )
        models.LikeList.objects.create(
            user=user,
            numCoins=request.POST.get('num_coins'),
            numFollowers=request.POST.get('num_followers')

        )
        return BaseView.success()
    '''
    edit user's information
    '''
    def editInfo(request):
        models.Users.objects. \
            filter(user__id=request.POST.get('id')).update(
            numCoins=request.POST.get('num_coins'),
            numFollowers=request.POST.get('num_followers')
        )
        return BaseView.success()
    '''
    delete user's information
    '''
    def delInfo(request):
        if (models.ReviewLogs.objects.filter(users__user__id=request.POST.get('id')).exists()):
            return BaseView.warning('There are associated relationships that cannot be deleted')
        models.Users.objects.filter(id=request.POST.get('id')).delete()
        return BaseView.success()

'''
Display admin information
'''

class AdminsView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'page':
            return AdminsView.getPageInfo(request)
        # elif module == 'get':
        #     return AdminsView.get_admin_info(request)
        else:
            return BaseView.error()
    def post(self, request, module, *args, **kwargs):
        if module == 'add':
            return AdminsView.addInfo(request)
        elif module == 'edit':
            return AdminsViewsView.editInfo(request)
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

        adminName = request.GET.get('adminName')
        adminIntro = request.GET.get('adminIntro')
        adminLoginTime = request.GET.get('adminLoginTime')

        query = Q()

        if adminName:
            query &= Q(adminName__icontains=adminName)
        if adminIntro:
            query &= Q(intro__icontains=adminIntro)
        if adminLoginTime:
            query &= Q(logintime__icontains=adminLoginTime)
        data = models.Admins.objects.filter(query)

        paginator = Paginator(data, page_size)
        resl = []
        for item in list(paginator.page(page_index)):
            temp = {
                'id': item.user.id,
                'userName': item.user.userName,
                'passWord': item.uesr.passWord,
                'adminName': item.user.name,
                'adminIntro': item.user.intro,
                'adminLoginTime': item.loginTime
            }
            resl.append(temp)
        pageData = BaseView.parsePage(int(pageIndex), int(pageSize),
                                       paginator.page(pageIndex).paginator.num_pages,
                                       paginator.count, resl)

        return BaseView.successData(pageData)
    '''
    add admins' information
    '''
    @transaction.atomic
    def addInfo(request):
        if models.Admins.objects.filter(username=request.POST.get('username')).exists():
            return BaseView.warning('This account already exists, please re-enter.')
        user = models.Admins.objects.create(
            username=request.POST.get('username'),
            password=request.POST.get('password'),
            name = request.POST.get('name'),
            email=request.POST.get('email'),
            gender=request.POST.get('gender'),
            age=request.POST.get('age'),
            type=0
        )

        models.Users.objects.create(
            user=user,
            intro = request.POST.get('intro'),
            loginTime = request.POST.get('loginTime')
        )
        return BaseView.success()
    '''
    edit admins' information
    '''
    def editInfo(request):
        models.Admins.objects. \
            filter(user__id=request.POST.get('id')).update(
            intro=request.POST.get('intro'),
            loginTime=request.POST.get('loginTime')
        )
        return BaseView.success()

    '''
    delete admins' information
    '''
    def deleteInfo(request):
        if (models.Admins.objects.filter(admin__user__id=request.POST.get('id')).exists()):
            return BaseView.warning('There are associated relationships that cannot be deleted')
        models.Admins.objects.filter(id=request.POST.get('id')).delete()
        return BaseView.success()

'''
movies' information management
'''
class MoviesView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'page':
            return MovieView.getPageInfo(request)
        elif module == 'info':
            return MovieView.getInfo(request)
        elif module == 'search':
            return MoviesView.searchInfo(request)
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
    gain movie info
    '''
    def getInfo(request):
        movie_data = models.Movies.objects.filter(id=request.GET.get('id')).first()
        resl = {
            'id': movie_data.id,
            'movie_name': movie_data.name,
            'movie_intro': movie_data.intro,
            'release_time': movie_data.release_time,
            'genre': movie_data.genre,
            'status':movie_data.status,
            'producer': movie_data.producer,
            'adminName': movie_data.admin.users.name,
            'adminGender': movie_data.admin.users.gender,
            'adminAge': movie_data.admin.users.age,
            'adminEmail': movie_data.admin.users.email,
            'adminIntro': movie_data.admins.intro,
            'adminLoginTime': movie_data.admins.login_time
        }
        return BaseView.successData()
    '''
    Viewing movie information by pagination
    '''
    def getPageInfo(request):

        loginUser = SysView.getLoginUser(request.GET.get('token'))

        pageIndex = request.GET.get('pageIndex', 1)
        pageSize = request.GET.get('pageSize', 10)
        MovieName = request.GET.get('adminName')
        ReviewsName = request.GET.get('moviesName')
        query = Q()
        if loginUser['type'] == 0:
            query = query & Q(admin__user__id=loginUser['id'])
        if BaseView.isExit(adminName):
            query = query & Q(admin__user__name__contains=adminName)
        if BaseView.isExit(MovieName):
            query = query & Q(name__contains=MovieName)
        data = models.Movies.objects.filter(query).order_by('-release_time')
        paginator = Paginator(data, pageSize)
        resl = []
        for item in list(paginator.page(pageIndex)):
            temp = {
                'id': item.id,
                'movieName': item.movieName,
                'movieIntro': item.movieIntro,
                'releaseTime': item.releaseTime,
                'genre': item.genre,
                'producer': item.producer,
                'status': item.status,
                'adminName': item.admins.users.name,
                'adminGender': item.admins.users.gender,
                'adminEmail': item.admins.users.email,
                'adminAge': item.admins.users.age,
                'adminIntro': item.admins.intro,
                'adminLoginTime': item.admins.login_time
            }
            resl.append(temp)
        pageData = BaseView.parasePage(int(pageIndex), int(pageSize),
                                       paginator.page(pageIndex).paginator.num_pages,
                                       paginator.count, resl)

        return BaseView.successData(pageData)

    '''
    search movies' info according to genre
    '''

    def searchInfo(request):
        genre = request.GET.get('genre')
        movies = models.Movies.objects.filter(genre=genre)
        resl = []
        for movie in movies:
            temp = {
                'id': movie.id,
                'movieName': movie.movieName,
                'movieIntro': movie.movieIntro,
                'releaseTime': movie.releaseTime,
                'genre': movie.genre,
                'producer': movie.producer,
                'status': movie.status,
                'adminName': movie.admins.users.name,
                'adminGender': movie.admins.users.gender,
                'adminEmail': movie.admins.users.email,
                'adminAge': movie.admins.users.age,
                'adminIntro': movie.admins.intro,
                'adminLoginTime': movie.admins.login_time
            }
            resl.append(temp)
        return BaseView.successData(resl)

    '''
    add Movies' info
    '''
    def addInfo(self):
        loginUser = SystemView.getUserLogin(request.POST.get('token'))
        models.Movies.objects.create(
            admin=models.Admins.objects.filter(user__id=loginUser['id']).first(),
            movieName=request.POST.get('name'),
            movieIntro=requests.POST.get('intro'),
            releaseTime=time.strftime("%Y-%m-%d", time.localtime()),
            genre=requests.POST.get('genre'),
            status=0,
            producer=requests.POST.get('producer'),
        )
        return BaseView.success()
    def editInfo(request):
        models.Movies.objects. \
            filter(id=request.POST.get('id')).update(
            movieName=request.POST.get('movieName'),
            movieIntro=request.POST.get('movieIntro'),
            releaseTime=request.POST.get('releaseTime'),
            genre=request.POST.get('genre'),
            producer=request.POST.get('producer')
        )
        return BaseView.success()
    def deleteInfo(request):
        if (models.Movies.objects.filter(movie__admin__id=request.POST.get('id')).exists()):
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
            return ReviewLogsView.confirmReview(request)
        else:
            return BaseView.error()

    '''
    View movie review records by pageination
    '''
    def getPageInfo(request):
        loginUser = SystemView.getLoginUser(request.GET.get('token'))
        pageIndex = request.GET.get('pageIndex', 1)
        pageSize = request.GET.get('pageSize', 10)
        userName = request.GET.get('userName')
        movieName = request.GET.get('movieName')
        query = Q()
        if loginUser['type'] == 0:
            query = query & Q(movie__admin__user__id=loginUser['id'])
        if loginUser['type'] == 1:
            query = query & Q(user__user__id=loginUser['id'])
        if BaseView.isExist(userName):
            query = query & Q(user__user__name__contains=userName)
        if BaseView.isExist(movieName):
            query = query & Q(movie__name__contains=movieName)
        data = models.ReviewLogs.objects.filter(query).order_by("-review_time")
        paginator = Paginator(data, pageSize)
        resl = []
        for item in list(paginator.page(pageIndex)):
            temp = {
                'id':item.id,
                'userName': item.user.users.name,
                'userNumOfCoins': item.user.num_coins,
                'userNumOfFollowers': item.user.num_followers,
                'movieId': item.movies.id,
                'movieName': item.movies.movie_name,
                'adminName': item.admins.users.name,
                'adminIntro': item.admins.intro,
                'adminLoginTime': item.admins.login_time,
                'reviewTime': item.review_time,
                'comments': item.comments,
                'ratings': item.ratings
            }
            resl.append(temp)
        pageData = BaseView.parasePage(int(pageIndex), int(pageSize),
                                       paginator.page(pageIndex).paginator.num_pages,
                                       paginator.count, resl)

        return BaseView.successData(pageData)
    '''
    add review logs
    '''
    @transaction.atomic
    def addInfo(request):
        loginUser = SystemView.getUserLogin(request.POST.get('token'))
        review = models.User.objects.filter(id=request.POST.get('movieId'))
        models.ReviewLogs.objects.create(
            user=models.User.objects.filter(user__id=loginUser['id']).first(),
            movie=movie.first(),
            review_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        )
        movie.update(
            commentedPerson=movie.first().commentedPerson + 1

        )
        return BaseView.success()
    def editInfo(request):
        models.ReviewLogs.objects. \
            filter(id=request.POST.get('id')).update(
            comments=request.POST.get('comments'),
            ratings=request.POST.get('ratings')
        )
        return BaseView.success()
'''
favoriate list management
'''
class FavoriateListsView(BaseView):
    def get(self, request, module, *args, **kwargs):
        if module == 'page':
            return FavoriateListsView.getPageInfo(request)
        elif module == 'info':
            return FavoriateListsView.getInfo(request)
        else:
            return BaseView.error()

    def post(self, request, module, *args, **kwargs):
        if module == 'add':
            return FavoriateListsView.addInfo(request)
        else:
            return BaseView.error()

    '''
    gain related favoriate list info
    '''
    def getInfo(request):
        favoriate = models.FavoriateLists.objects.filter(id=request.GET.get('id')).first()
        resl = {
            'id': favoriate.id,
            'collectTime':favoriate.collectTime,
        }
        return BaseView.successData(resl)
    '''
    View favorite list by page
    
    '''
    def getPageInfo(request):
        loginUser = SysView.getLoginUser(request.GET.get('token'))

        pageIndex = request.GET.get('pageIndex', 1)
        pageSize = request.GET.get('pageSize', 10)
        studentName = request.GET.get('studentName')
        projectName = request.GET.get('projectName')

        query = Q(movie__isnull=False);
        if loginUser['type'] == 0:
            query = qruery & Q(movie__admin__user__id=loginUser['id'])
        elif loginUser['type'] == 1:
            query = qruery & Q(user__id=loginUser['id'])

        if BaseView.isExit(studentName):
            query = qruery & Q(user__name__contains=userName)
        if BaseView.isExit(projectName):
            query = qruery & Q(movie__admin__name__contains=movieName)

        data = models.User.objects.filter(query)

        paginator = Paginator(data, pageSize)

        resl = []
        for item in list(paginator.page(pageIndex)):
            temp = {
                'userId': item.user.users.id,
                'userName': item.user.users.name,
                'userNumOfCoins': item.user.num_coins,
                'userNumOfFollowers': item.user.num_followers,
                'movieId': item.movies.id,
                'movieName': item.movies.movie_name,
                'adminName': item.admins.users.name,
                'adminIntro': item.admins.intro,
                'adminLoginTime': item.admins.login_time,
            }
            resl.append(temp)

        pageData = BaseView.parasePage(int(pageIndex), int(pageSize),
                                       paginator.page(pageIndex).paginator.num_pages,
                                       paginator.count, resl)

        return BaseView.successData(pageData)

    '''
    add favoriate list info
    '''
    def addInfo(request):
        models.FavoriateLists.objects.create(
            collectTime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        )
        return BaseView.success()



































