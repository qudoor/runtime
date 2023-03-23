import os
import platform
from apps.common.documentation.description import description

if platform.system() == 'Darwin' and platform.machine() == 'arm64':
    import pymysql

    pymysql.version_info = (1, 4, 2, "final", 0)
    pymysql.install_as_MySQLdb()

from .. import const
from ..const import CONFIG

BASE_DIR = const.BASE_DIR

# 新增一个系统导包路径
import sys

sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = CONFIG.SECRET_KEY

DEBUG = CONFIG.DEBUG

LOG_LEVEL = CONFIG.LOG_LEVEL

ALLOWED_HOSTS = ['*']

CORS_ORIGIN_WHITELIST = (
    'http://127.0.0.1:8000',
)
CORS_ALLOW_CREDENTIALS = False

PWD_ENCRYPTION = CONFIG.PWD_ENCRYPTION

DB_OPTIONS = {}
DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': CONFIG.DB_NAME,
        'HOST': CONFIG.DB_HOST,
        'PORT': CONFIG.DB_PORT,
        'USER': CONFIG.DB_USER,
        'PASSWORD': CONFIG.DB_PASSWORD,
        'ATOMIC_REQUESTS': True,
        'OPTIONS': DB_OPTIONS
    }
}

REDIS_SETTING = {
    'host': CONFIG.REDIS_HOST,
    'port': CONFIG.REDIS_PORT,
}

CACHES = {
    # default 是缓存名，可以配置多个缓存
    "default": {
        # 应用 django-redis 库的 RedisCache 缓存类
        "BACKEND": "django_redis.cache.RedisCache",
        # 配置正确的 ip和port
        "LOCATION": 'redis://{0}:{1}/2'.format(REDIS_SETTING['host'], REDIS_SETTING['port']),
        "OPTIONS": {
            # redis客户端类
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # redis连接池的关键字参数
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100
            }
        }
    },
    "task_caches": {
        # 应用 django-redis 库的 RedisCache 缓存类
        "BACKEND": "django_redis.cache.RedisCache",
        # 配置正确的 ip和port
        "LOCATION": 'redis://{0}:{1}/3'.format(REDIS_SETTING['host'], REDIS_SETTING['port']),
        "OPTIONS": {
            # redis客户端类
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # redis连接池的关键字参数
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100
            }
        }
    }
}

# channels channel_layers 使用 redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            # "hosts": [(REDIS_SETTING['host'], REDIS_SETTING['port'])],
            "hosts": ["redis://" + str(REDIS_SETTING['host']) + ':' + str(REDIS_SETTING['port']) + "/1"],
            # "hosts": ["redis://x.x.x.195:6379/1"],
        },
    },
}

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    # 跨域组件
    'corsheaders',
    'channels',
    # 健康检查
    'health_check',
]

LOCAL_APPS = [
    'common.apps.CommonConfig',
    'ops.apps.OpsConfig',
    'runtime.apps.RuntimeConfig',
    'apps.auth.user',
    'apps.common.documentation',
    'apps.common.tracking',
]

# 所有应用
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.auth.user.authentications.JwtAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
        'djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer',
        # Any other renders
    ),

    'DEFAULT_PARSER_CLASSES': (
        # If you use MultiPartFormParser or FormParser, we also have a camel case version
        'djangorestframework_camel_case.parser.CamelCaseFormParser',
        'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        # Any other parsers
    ),

    # 异常处理
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    # 文档
    'DEFAULT_SCHEMA_CLASS': 'apps.common.documentation.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'apps.common.drf.pagination.MyPageNumberPagination',
}

SPECTACULAR_SETTINGS = {
    'TITLE': "QuPot API",
    'DESCRIPTION': description,
    'LICENSE': {
        'name': 'MIT License'
    },
    "SERVERS": [
        {
            "url": "http://127.0.0.1:9001/",
            "description": "Local server"
        },
        {
            "url": "http://x.x.x.212/",
            "description": "Development server"
        },
        {
            "url": "http://x.x.x.212/",
            "description": "Production server"
        }
    ],
    'VERSION': 'v1',
    'CONTACT': {
        'name': "QuDoor Team",
        "email": "admin@qudoor.cn",
    },

    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api',
    'DISABLE_ERRORS_AND_WARNINGS': True,
    'ENABLE_DJANGO_DEPLOY_CHECK': False,

    'SWAGGER_UI_DIST': 'SIDECAR',
    # 'SWAGGER_UI_DIST': 'https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.15.2',
    'SWAGGER_UI_FAVICON_HREF': '/static/favicon.ico',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'docExpansion': 'none',
        'showExtensions': True,
        'showCommonExtensions': True,
        'syntaxHighlight.theme': 'arta',
        "displayOperationId": True,
        # 'syntaxHighlight': False
        # 'tryItOutEnabled': True
        # 'requestSnippetsEnabled': True,
    },

    'SERVE_URLCONF': "QuPot.urls",
    'CAMELIZE_NAMES': True,
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
        'drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields',
    ],
}

# Django 会尝试对所有的"认证后端(backend)"进行认证。如果第一个认证方法失败，Django 就尝试第二个，以此类推，直到所有后端都尝试过。
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.common.middleware.csrf_middleware.NotUseCsrfTokenMiddlewareMixin',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.common.tracking.middleware.ApiTrackingMiddleware',
]

ROOT_URLCONF = 'QuPot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'QuPot.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = "user.User"

# 修改使用中文界面
LANGUAGE_CODE = 'zh-Hans'
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'QuPot/locale/')
]

# 修改时区
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# STATICFILES_DIRS的作用是，在app中没有找到对应的文件时也会在其指定的目录下去寻找文件
STATICFILES_DIRS = [
    # os.path.join(BASE_DIR, 'static'),
]
# 访问上传文件的url地址前缀
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 添加 websocket 支持
ASGI_APPLICATION = "QuPot.routing.application"
TMP_DIR = os.path.join(BASE_DIR, 'tmp')

# 事务回滚
ATOMIC_REQUESTS = True

# kubernetes 路径
K8S_CONFIG = os.path.join(BASE_DIR, "data/kubernetes")
if not os.path.exists(K8S_CONFIG):
    os.makedirs(K8S_CONFIG)

# 监听地址
HTTP_HOST = CONFIG.HTTP_HOST
# QuPot端口
HTTP_PORT = CONFIG.HTTP_PORT
WS_PORT = CONFIG.WS_PORT
FLOWER_PORT = CONFIG.FLOWER_PORT

# celery task
SHORT_TIMEOUT = 5

# ansible 配置
ANSIBLE_CONNECTION_TYPE = 'ssh'
PlayBOOK_OPTIONS = {
    'timeout': 400,
    'forks': 10,
    'become': True,
    'become_method': "sudo",
    'become_user': "root",
}

# playbook 路径
PLAYBOOK_ROOT = os.path.join(BASE_DIR, "playbook")
if not os.path.exists(PLAYBOOK_ROOT):
    os.makedirs(PLAYBOOK_ROOT)

NEXUS_NAME = CONFIG.NEXUS_NAME

# helm工具路径
HELM_BINARY_PATH = CONFIG.HELM_BINARY_PATH
# 应用商店使用的namespace
APPSTORE_NAMESPACE = CONFIG.APPSTORE_NAMESPACE
