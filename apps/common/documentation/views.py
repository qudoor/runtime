from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.settings import patched_settings, spectacular_settings
from drf_spectacular.plumbing import get_relative_url, set_query_parameters


class BaseDocsView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    authentication_classes = ()
    permission_classes = ()

    url_name = 'schema'
    url = None
    template_name = None
    title = spectacular_settings.TITLE

    def _get_schema_url(self, request):
        schema_url = self.url or get_relative_url(reverse(self.url_name, request=request))
        return set_query_parameters(
            url=schema_url,
            lang=request.GET.get('lang'),
            version=request.GET.get('version')
        )


class ElementsView(BaseDocsView):
    template_name = 'documentation/elements.html'

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        return Response(
            data={
                'title': self.title,
                'schema_url': self._get_schema_url(request),
            },
            template_name=self.template_name,
        )
