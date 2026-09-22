from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response

from .serializers import AcceptanceSerializer, ConsentSerializer, DeletionSerializer
from .services import privacy_service


class LegalDocumentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request, document):
        spec = privacy_service.documents().get(document)
        if spec is None:
            return error_response("Unknown legal document.", status_code=404)
        return success_response(data={"document": document, **spec})


class ConsentView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ConsentSerializer

    def post(self, request):
        serializer = ConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        consent = privacy_service.record_consent(user=user, **serializer.validated_data)
        return success_response(data={"id": str(consent.id)}, status_code=201)


class AcceptanceView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AcceptanceSerializer

    def post(self, request):
        serializer = AcceptanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        acceptance = privacy_service.accept(
            user=request.user, document=serializer.validated_data["document"]
        )
        return success_response(
            data={"document": acceptance.document, "version": acceptance.version}
        )


class ExportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return success_response(
            data=privacy_service.export_user(request.user), message="Export ready"
        )


class DeletionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeletionSerializer

    def post(self, request):
        serializer = DeletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            privacy_service.delete_account(
                user=request.user, reason=serializer.validated_data.get("reason", "")
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)
        return success_response(message="Account scheduled for deletion")
