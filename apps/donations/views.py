from apps.donations.models import Donation
from apps.projects.models import Project
from apps.donations.serializers import DonationSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
# Create your views here.

class DonationList(APIView):
      permission_classes = [IsAuthenticated]

      def get(self,request):
            project_donations = Donation.objects.filter(user=request.user) 
            serializer = DonationSerializer(project_donations,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)  


class DonationCreateRetrieve(APIView):
      permission_classes = [IsAuthenticated]

      def get(self,request,project_id):
          if(Project.objects.filter(id=project_id).exists()):
            project_donations = Donation.objects.filter(project=project_id , user=request.user) 
            serializer = DonationSerializer(project_donations,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
          else:
            return  Response({"msg":"no project found"},status=status.HTTP_404_NOT_FOUND)
        
      def post(self,request,project_id):
          project = get_object_or_404(Project, id=project_id)
          if(project.status != "pending"):
            return Response({"msg":f"This project is already {project.status}"},status=status.HTTP_400_BAD_REQUEST)
      
          serializer = DonationSerializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          project.current_money += serializer.validated_data.get('amount',0.0)
          if (project.current_money >= project.target):
            project.status = "finished"
          project.save()
          serializer.save(user=request.user, project=project)
          return Response(serializer.data ,status=status.HTTP_201_CREATED)



    