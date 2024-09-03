#================================================GLOBAL_IMPORT==================================================
import json
import string
import random
from drf_yasg import openapi
from datetime import datetime
from django.conf import settings
from rest_framework import status
from collections import OrderedDict
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view,permission_classes
from rest_framework.generics import GenericAPIView
from django.core.exceptions import ObjectDoesNotExist,ValidationError
from django.utils.timezone import make_aware
from datetime import date,time,timezone
from zoneinfo import ZoneInfo
from django.utils.dateparse import parse_date


#================================================LOCAL_IMPORT==================================================

from virtual_conference.settings import *
from core.serializer import *
from core.models import *
from core.mixin import *

#================================================DEFAULT_VIEW=================================================

class DefaultAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve a greeting message",
        responses={200: openapi.Response('A greeting message', schema=openapi.Schema(
            type=openapi.TYPE_STRING,
            description="The greeting message"
        ))}
    )
    def get(self, request):
        data = {
            "hii, Welcome to ISEA International conference"
        }
        return Response(data)

#================================================LOGIN/USER_MANAGEMENT========================================================

ivp_login_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the user'),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the user'),
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Mobile number or username of the user'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role of the user'),
        'unique_id': openapi.Schema(type=openapi.TYPE_STRING, description='Unique ID of the user')
    },
    required=['first_name', 'last_name', 'username', 'email', 'user_id', 'role', 'unique_id']
)

ivp_login_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        # 'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status of the request'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message'),
        # 'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description='HTTP status code')
    }
)
class IvpLogin(APIView):
    @swagger_auto_schema(
        operation_description= "Login for users",
        request_body=ivp_login_request_schema,
        responses={200: ivp_login_response_schema}
    )
    def post(self, request):
        try:
            data = OrderedDict()
            data.update(request.data)
            try:
                first_name = data['first_name']
                last_name = data['last_name']
                # mobileno = data['mobile_number']
                mobileno = data['username']
                email = data['email']
                username = data['username']
                k_id = data['user_id']
                role = data['role']
                unique_id = data['unique_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            encrypt_data = data_encrypt(email = email, mobileno = mobileno, first_name = first_name,
                                         last_name = last_name, username = username, unique_id = unique_id)
            encrypt_data['is_active'] = 1
            encrypt_data['k_id'] = k_id
            check_email = AuthUser.objects.filter(email = encrypt_data['email']).exists()
            check_phone = AuthUser.objects.filter(mobileno = encrypt_data['mobileno']).exists()
            if check_email and check_phone:
                user = AuthUser.objects.get(email = encrypt_data['email'])
                login_time = {"last_login": datetime.now(), 'unique_id': encrypt_data['unique_id']}
                serializer = LastloginSerializer(user, data = login_time)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:
                encrypt_data['last_login'] = datetime.now()
                serializer = LoginSerializer(data = encrypt_data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                group_id = AuthGroup.objects.get(name = role)
                ug_data = {"user": user.pk, "group": group_id.pk}
                ug_serializer = UserGroupSerializer(data = ug_data)
                ug_serializer.is_valid(raise_exception=True)
                ug_serializer.save()
            return Response({"status": 0,"message": "Login successful",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
            # return Response({"error": str(e)})

user_details_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID')
    },
    required=['user_id']
)

user_details_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        # 'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status of the request'),
        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Decrypted user details'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message'),
        # 'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description='HTTP status code')
    }
)
class UserDetails(APIView):

    @swagger_auto_schema(
        operation_description= "Show user details by id",
        request_body=user_details_request_schema,
        responses={200: user_details_response_schema}
    )

    def post(self, request):
        try:
            try:
                k_id = request.data['user_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            user = AuthUser.objects.get(k_id = k_id)
            group = AuthUserGroups.objects.get(user = user.pk)
            serializer = ShowUserSerializer(user)
            data = serializer.data
            decrypt = data_decrypt(first_name = data['first_name'], last_name= data['last_name'], username = data['username'],
                                       mobileno = data['mobileno'],email = data['email'])
            decrypt['role'] = group.group.name
            decrypt['user_id'] = data['id']
            return Response({"status": 0,"data": decrypt,"message": "User details fetched successfully",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
            # return Response({"error": str(e)})

all_user_details_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        # 'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status of the request'),
        'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT), description='List of decrypted user details'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message'),
        # 'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description='HTTP status code')
    }
)

class AllUserDetails(APIView):

    @swagger_auto_schema(
        operation_description= "Show all existing user details",
        responses={200: all_user_details_response_schema}
    )
     
    def get(self, request):
        try:
            
            user = AuthUser.objects.all()
            # group = AuthUserGroups.objects.get(user = user.pk)
            serializer = ShowUserSerializer(user, many = True)
            list = []
            for data in serializer.data:
                group = AuthUserGroups.objects.get(user = data['id'])

                decrypt = data_decrypt(first_name = data['first_name'], last_name= data['last_name'], username = data['username'],
                                       mobileno = data['mobileno'],email = data['email'])
                decrypt['role'] = group.group.name
                decrypt['user_id'] = data['id']
                list.append(decrypt)
            return Response({"status": 0,"data": list,"message": "User details fetched successfully",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
            # return Response({"error": str(e)})


#================================================CONFERENCE_MANAGEMENT========================================================

event_create_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the event'),
        'shortform': openapi.Schema(type=openapi.TYPE_STRING, description='Shortform of the event'),
        'orga_email': openapi.Schema(type=openapi.TYPE_STRING, description='Organizer email'),
        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Start date of the event'),
        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='End date of the event'),
        'logo': openapi.Schema(type=openapi.TYPE_STRING, description='Logo of the event'),
        'created_by': openapi.Schema(type=openapi.TYPE_STRING, description='Creator of the event'),
        'track_id': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='Track IDs of the event')
    },
    required=['name', 'shortform', 'orga_email', 'start_date', 'end_date', 'logo', 'created_by', 'track_id']
)

event_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        # 'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status of the request'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)

event_detail_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the event')
    },
    required=['event_id']
)

event_detail_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        # 'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status of the request'),
        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Event data'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)

class EventView(GenericAPIView):
    
    @swagger_auto_schema(
        method='post',
        operation_description= "Create a conference by receiving necessary data",
        request_body=event_create_request_schema,
        responses={200: event_response_schema}
    )
    @api_view(['post'])
    def CreateEventView(request):
        try:
            data = request.data.copy()
            try:
                data['name']
                data['shortform']
                data['orga_email']
                data['start_date']
                data['end_date']
                data['logo']
                data['created_by']
                data['track_id']
            except KeyError as e:
                    return Response({"status": 1, "errors": f"Necessary Field {e} is not available in the request",
                                "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_204_NO_CONTENT)
            if Event.objects.filter(shortform = data['shortform']).exists():
                raise serializers.ValidationError({
                    "errors":"Shortform with this name already exists please try with another."
                })
            track = []
            for t in data["track_id"]:
                track.append(t)
            track = [element for element in track if element != ',']           
            data['track_id'] = json.dumps(track)
            validate_logo = validate_img(data['logo'])
            if validate_logo == False:
                return Response({
                        "status": 0,
                        "errors": "Invalid file extention, only 'jpg', 'jpeg' and 'png' are allowed",
                        "status_code": 415
                        },status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            if validate_logo:
                data['logo'] = uploadLogo(request.FILES['logo'], request, EVENT_LOGO_DIR, data['shortform'])
            validate_header_image = validate_img(data['header_image'])
            if validate_header_image == False:
                return Response({
                        "status": 0,
                        "errors": "Invalid file extention, only 'jpg', 'jpeg' and 'png' are allowed",
                        "status_code": 415
                        },status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            if validate_header_image:
                data['header_image'] = uploadHeaderImage(request.FILES['header_image'], request, EVENT_HEADER_IMAGE_DIR, data['shortform'])
            data['created_on'] = datetime.now()
            serializer = CreateEventSerializer(data = data)
            if not serializer.is_valid():
                error = serializer.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                        "errors": formatted_errors
                    })
            eventID = serializer.save()
            CreateEventId(eventID.pk)
            return Response({"status": 0, "message": "Successfully Created the Event",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     return Response({"error": str(e)})

    @swagger_auto_schema(
        method='post',
        operation_description= "Show details of conference based on its ID",
        request_body=event_detail_request_schema,
        responses={200: event_detail_response_schema}
    )
    @api_view(['post'])
    def ShowEventByIdView(request):
        try:
            try:
                eventId = request.data['event_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            serialzer = ShowEventSerializer(event)
            data = serialzer.data
            try:
                data['logo'] = env("BASE_URL") + EVENT_LOGO_DIR + data['logo']
            except:
                pass
            try:
                data['header_image'] = env("BASE_URL") + EVENT_HEADER_IMAGE_DIR + data['header_image']
            except:
                pass
            data['track'] = json.loads(data['track_id'])
            trackData = []
            for track in data['track']:
                try:
                    track_data = Track.objects.get(id = track)
                except Track.DoesNotExist:
                    return Response({"status": 0, "errors": [], "errors": "Track Not Found",
                              "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
                payload = {"track_id": track_data.pk, "track_name": track_data.track_name}
                trackData.append(payload)
            # data.pop(track)
            data['track'] = trackData

            return Response({"data": data,  "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     return Response({"error": str(e)})

    @swagger_auto_schema(
        method='get',
        operation_description= "Show all existing conference details",
        responses={200: event_detail_response_schema}
    )
    @api_view(['get'])
    def ShowAllEventview(request):
        try:
            event = Event.objects.all()
            serializer = ShowEventSerializer(event, many = True)
            list = []
            for data in serializer.data:
                try:
                    data['logo'] = env("BASE_URL") + EVENT_LOGO_DIR + data['logo']
                except:
                    pass
                try:
                    data['header_image'] = env("BASE_URL") + EVENT_HEADER_IMAGE_DIR + data['header_image']
                except:
                    pass
                data['track_id'] = json.loads(data['track_id'])
                list.append(data)
            return Response({"status": 0, "data": list,"message": "Successfully Fetched the event",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     return Response({"error": str(e)})

    @swagger_auto_schema(
        method='get',
        operation_description= "Show details of upcoming 5 conferences in ascending order",
        responses={200: event_detail_response_schema}
    )
    @api_view(['get'])
    def ShowUpcomingEventView(request):
        try:
            event = Event.objects.all()
            current_date = date.today()
            serializer = ShowEventSerializer(event, many = True)
            upcoming_events = []
            for data in serializer.data:
                event_start_date = parse_date(data['start_date'])
                if event_start_date > current_date:
                    try:
                     data['logo'] = env("BASE_URL") + EVENT_LOGO_DIR + data['logo']
                    except:
                        pass
                    try:
                        data['header_image'] = env("BASE_URL") + EVENT_HEADER_IMAGE_DIR + data['header_image']
                    except:
                        pass
                    data['track_id'] = json.loads(data['track_id'])
                    upcoming_events.append(data)
            upcoming_events.sort(key=lambda event: parse_date(event['start_date']))
            return Response({"status": 0, "data": upcoming_events[:5],"message": "Successfully Fetched the upcoming events",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='patch',
        operation_description= "Update details of any particular conference",
        request_body=event_create_request_schema,
        responses={200: event_response_schema}
    )
    @api_view(['patch'])
    def UpdateEventView(request):
        try:
            data = request.data.copy()
            try:
                eventId = request.data['id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if "logo" in data:
                validate_logo = validate_img(data['logo'])
                if validate_logo == False:
                    return Response({
                            "status": 0,
                            "errors": "Invalid file extention, only 'jpg', 'jpeg' and 'png' are allowed",
                            "status_code": 415
                            },status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
                if validate_logo:
                    data['logo'] = uploadLogo(request.FILES['logo'], request, EVENT_LOGO_DIR, event.shortform)
            if "header_image" in data:
                validate_header_image = validate_img(data['header_image'])
                if validate_header_image == False:
                    return Response({
                            "status": 0,
                            "errors": "Invalid file extention, only 'jpg', 'jpeg' and 'png' are allowed",
                            "status_code": 415
                            },status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
                if validate_header_image:
                    data['header_image'] = uploadHeaderImage(request.FILES['header_image'], request, EVENT_HEADER_IMAGE_DIR, event.shortform)
            data['id'] = eventId
            data['updated_on'] = datetime.now()
            if 'track_id' in data:
                data['track_id'] = json.dumps(data['track_id'])
            serializer = UpdateEventSerializer(event, data = data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"status": 0, "message": "Successfully Updated the Event Track",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     return Response({"error": str(e)})



#================================================TRACK_MANAGEMENT========================================================

create_track_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'track_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the track'),
        'topic': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING),
            description='List of topics associated with the track'
        )
    },
    required=['track_name', 'topic']
)

show_track_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'track_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the track')
    },
    required=['track_id']
)

track_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)

track_detail_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Track data'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)

class TrackView(GenericAPIView):
    
    @swagger_auto_schema(
        method='post',
        operation_description= "Create a track under a conference and multiple topics under the same track",
        request_body=create_track_request_schema,
        responses={200: track_response_schema}
    )
    @api_view(['post'])
    def CreateTrackView(request):
        try:
            track_data = OrderedDict()
            try:
                track_data['track_name'] = request.data.get('track_name')
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            topics = request.data.get('topic')
            track_data['updated_on'] = datetime.now()
            if Track.objects.filter(track_name = track_data['track_name']).exists():
                return Response({
                    "message": "A track with same name already exists",
                    "status_code": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)
            serializer = CreateTrackSerializer(data = track_data)
            serializer.is_valid(raise_exception=True)
            track = serializer.save()
            CreateTrackId(track.pk)
            if not topics:
                return Response({
                    "status": 0,
                    "errors": "Topics are required",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except json.JSONDecodeError:
                    return Response({
                        "status": 0,
                        "errors": "Invalid topics format",
                        "status_code": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST)
            for topic in topics:
                topic_data = {
                    'trackid': track.pk,
                    'topic': topic
                }
                topic_serializer = CreateTopicSerializer(data=topic_data)
                topic_serializer.is_valid(raise_exception=True)
                topic_serializer.save()
            return Response({"status": 0,"message": "Successfully Created the Event Track and Topic",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     return Response({"error": str(e)})

    @swagger_auto_schema(
        method='post',
        operation_description= "Show track of conference by id along with the topics under it",
        request_body=show_track_request_schema,
        responses={200: track_detail_response_schema}
    )
    @api_view(['post'])
    def ShowTrackByIdView(request):
        try:
            try:
                trackId = request.data['track_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                track = Track.objects.get(id = trackId)
            except Track.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Track Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            serialzer = ShowTrackSerializer(track)
            data = serialzer.data
            top = Topic.objects.filter(trackid = data['id'])
            serializer1 = ShowTopicSerializer(top, many=True)
            data['topic'] = serializer1.data
            # if data['topic'] != None:
            #     data['topic'] = json.loads(data['topic'])
            return Response({"status": 0, "data": data,"message": "Successfully Fetched the event",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
    @swagger_auto_schema(
        method='get',
        operation_description= "Show all tracks present in database along with the topics under them",
        responses={200: track_detail_response_schema}
    )
    @api_view(['get'])
    def ShowAllTrackView(request):
        try:
            track = Track.objects.all()
            serializer = ShowTrackSerializer(track, many = True)
            list = []
            for data in serializer.data:
                # if data['topic'] != None:   
                #     data['topic'] = json.loads(data['topic'])
                top = Topic.objects.filter(trackid = data['id'])
                serializer1 = ShowTopicSerializer(top, many=True)
                data['topic'] = serializer1.data
                list.append(data)
            return Response({"status": 0, "data": list,"message": "Successfully Fetched the event track",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     return Response({"error": str(e)})

    @swagger_auto_schema(
        method='patch',
        operation_description= " add an extra topic under the track",
        request_body=create_track_request_schema,
        responses={200: track_response_schema}
    )
    @api_view(['patch'])
    def UpdateTrackView(request):
        try:
            data = request.data.copy()
            try:
                trackId = request.data['track_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                track = Track.objects.get(id = trackId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            data['id'] = trackId
            data['updated_on'] = datetime.now()
            # if 'track_name' in data:
            #     data['track_name'] = data['track_name']
            # serializer = UpdateTrackSerializer(track, data = data)
            # serializer.is_valid(raise_exception=True)
            # serializer.save()
            if 'topic' in data:
                for topic in data['topic']:
                    topic_data = {
                        'trackid': track.pk,
                        'topic': topic
                    }
                    topic_serializer = CreateTopicSerializer(data=topic_data)
                    topic_serializer.is_valid(raise_exception=True)
                    topic_serializer.save()
            return Response({"status": 0, "message": "Successfully added the topic",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)})

   
    @swagger_auto_schema(
        method='delete',
        operation_description= "Delete a topic",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                        'topic_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the track')
                        },
            required=['topic_id']
            ),
        responses={200: track_response_schema}
    )
    @api_view(['delete'])
    def DeleteTopicView(request):
        try:
            try:
                topicID = request.data['topic_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                topic = Topic.objects.get(id=topicID)
            except Topic.DoesNotExist:
                return Response({
                "status": 0,
                "errors": "Topic not found.",
                "status_code": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)
            topic.delete()
            return Response({
            "status": 0,
            "message": "Successfully deleted the topic.",
            "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#================================================ROLE_CHANGE========================================================

assign_role_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
        'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role to assign')
    },
    required=['email', 'role']
)

assign_role_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)
class AssignRole(APIView):
    @swagger_auto_schema(
        operation_description= "To assign a role",
        request_body=assign_role_request_schema,
        responses={200: assign_role_response_schema}
    )
    def post(self, request):
        try:
            data = request.data.copy()
            try:
                data['email']
                role = data['role']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            encrypt = data_encrypt(email = data['email'])
            try:
                user = AuthUser.objects.get(email = encrypt['email'])
                User_Group = AuthUserGroups.objects.get(user = user.pk)
            except (AuthUser.DoesNotExist, AuthUserGroups.DoesNotExist):
                return Response({"status": 0, "errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if role in ["Admin","User"]:
                return Response({"status": 0, "data": "data","errors": f"Role can not change to {role}",
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            if User_Group.group.name == role:
                    return Response({"status": 0, "data": "data","errors": f"User is already a {role}",
                              "status_code": status.HTTP_409_CONFLICT}, status=status.HTTP_409_CONFLICT)
            group = AuthGroup.objects.get(name = role)
            dict = {"user": user.pk, "group": group.pk}
            serializer = UserGroupSerializer(User_Group, data=dict)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"status": 0, "message": f"User role changed to {role}",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # except Exception as e:
            #     return Response({"error": str(e)})

class AssignReviewer(APIView):
    @swagger_auto_schema(
            operation_description="To assign a user the role of reviewer for an event",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
                'user_mail': openapi.Schema(type=openapi.TYPE_STRING, description='User Email')
            },
            required=['event_id', 'user_mail']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='User role changed to reviewer')
                }
            ),
        }
    )
    def post(self,request):
        try:
            data = {}
            try:
                data['event_id'] = request.data['event_id']
                request.data['user_mail']
            except KeyError as e:
                return Response({"errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                emailregex(request.data['user_mail'])
            except ValidationError:
                return Response({ "errors": "Not a valid email address",
                                "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            encrypt = data_encrypt(email = request.data['user_mail'])
            try:
                user = AuthUser.objects.get(email = encrypt['email'])
            except AuthUser.DoesNotExist:
                return Response({"errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if Reviewer.objects.filter(event_id=data['event_id'], user_id=user.pk).exists():
                return Response({
                    "message": "User is already a reviewer for this event",
                    "status_code": status.HTTP_200_OK
                }, status=status.HTTP_200_OK)
            data['user_id'] = user.pk
            ser = CreateReviewerSerializer(data = data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({ "message": "User role changed to reviewer",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DeleteReviewer(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reviewer_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Reviewer ID')
            },
            required=['reviewer_id']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Successfully deleted the reviewer')
                }
            ),
        }
    )
    def post(self,request):
        try:
            try:
                revID = request.data['reviewer_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                rev = Reviewer.objects.get(id=revID)
            except Reviewer.DoesNotExist:
                return Response({
                "status": 0,
                "errors": "Reviewer not found.",
                "status_code": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)
            rev.delete()
            return Response({
            "status": 0,
            "message": "Successfully deleted the reviewer.",
            "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            



#================================================COUNT========================================================

count_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'data': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of users'),
                'event_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of events'),
                'track_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of tracks')
            }
        ),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)
class Count(APIView):
    @swagger_auto_schema(
        operation_description= "To show the count of no. of events,users and tracks",
        responses={200: count_response_schema}
    )
    def get(self, request):
        # try:
            event_count = Event.objects.all().count()
            user_count  = AuthUser.objects.all().count()
            track_count = Track.objects.all().count()
        # counting no. of submissions and participants per event
            event = Event.objects.all()
            event_ser = ShowEventSerializer(event, many=True)
            event_data = event_ser.data
            count_per_event = []
            for event in event_data:
                eventId = event['id']
                sub = Submission.objects.filter(event_id = eventId)
                sub_count = sub.count()
                total_participant_list = []
                for submission in sub:
                    participant = submission.participants
                    total_participant_list = total_participant_list + participant
                total_participant_list = list(set(total_participant_list))
                participant_count = len(total_participant_list)
                sub_part_count = {"event_id":eventId, "submission_count":sub_count, "participant_count": participant_count}
                count_per_event.append(sub_part_count)
            data = {"user_count": user_count, "event_count": event_count, "track_count": track_count, "count_per_event": count_per_event}
            return Response({"data":data, "status": 0, "message": f"Counts",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        # except (TypeError, ValueError, NameError):
        #     return Response({"status": 0, "errors": "Something went wrong",
        #                         "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # except Exception as e:
            #     return Response({"error": str(e)})

#================================================SUBMISSION========================================================

class CheckUserRegistration(APIView):
    def post(self,request):
        try:
            try:
                request.data['email']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            encrypt = data_encrypt(mail = request.data['email'])
            try:
                user = AuthUser.objects.get(email = encrypt['mail'])
            except AuthUser.DoesNotExist:
                return Response({"status": 0, "errors": "User not registered with us. Kindly register the user to participate as a team.",
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            data = {}
            data['userId'] = user.pk
            return Response({"status": 1, "data" : data,"message": "Succesfully fetched the user id",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

create_submission_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the submission'),
        'abstract': openapi.Schema(type=openapi.TYPE_STRING, description='Abstract of the submission'),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the submission'),
        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
        'track_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Track ID'),
        'topic_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Topic ID'),
        'paperupload': openapi.Schema(type=openapi.TYPE_STRING,description='Paper upload')
    },
    required=['title', 'abstract', 'description', 'user_id', 'event_id', 'track_id', 'topic_id', 'paperupload']
)

generic_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)

submissions_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'data': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Submission ID'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title'),
                'abstract': openapi.Schema(type=openapi.TYPE_STRING, description='Abstract'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
                'track_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Track ID'),
                'topic_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Topic ID'),
                'paperupload': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='List of paper uploads'),
                'created_on': openapi.Schema(type=openapi.TYPE_STRING, description='Creation date'),
                'updated_on': openapi.Schema(type=openapi.TYPE_STRING, description='Last update date'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Submission status')
            })
        ),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
    }
)

class UserSubmission(GenericAPIView):
    
    @swagger_auto_schema(
        method='post',
        operation_description= "To create a user submission",
        request_body=create_submission_request_schema,
        responses={200: generic_response_schema}
    )
    @api_view(['post'])
    def CreateSubmissionView(request):
        try:
            data = request.data
            try:
                data['title']
                data['description']
                data['paperupload'] 
                userId = data['user_id']
                eventId = data['event_id']
                trackId = data['track_id']
                topicId = data['topic_id']
                data['team_composition'] = data['team_composition'].lower()
            except KeyError as e:
                return Response({"status":0, "errors": f"Necessary Field {e} is not available in the request",
                                 "status_code": status.HTTP_204_NO_CONTENT},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                user = AuthUser.objects.get(id = userId)
            except AuthUser.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                track = Track.objects.get(id = trackId)
            except Track.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Track Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                topic = Topic.objects.get(id = topicId)
            except Topic.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Topic Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if Submission.objects.filter(user_id=userId,event_id=eventId,track_id=trackId,topic_id=topicId).exists():
                return Response({
                    "message": f"User already made submission for the same track and topic in the conference {event.name}",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            # try:
            #     abs = Abstract.objects.get(user_id = userId, event_id=eventId,track_id=trackId,topic_id = topicId)
            # except Abstract.DoesNotExist:
            #     return Response({"status": 0, "errors": [], "errors": "Abstract Not Submitted.",
            #                       "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            # if abs.status=="Approved":
            data['created_on'] = date.today()
            obj = Event.objects.filter(id = data['event_id']).first()
            start_date = obj.start_date
            end_date = obj.end_date
            try:
                if isDateinRange(start_date, end_date, data['created_on']):
                    print("Date is within the range")
                    data['status'] = "Submitted"
                else:
                    print("Date is not within the range")
                    return Response({
                        "status": 0,
                        "errors": "Submissions are currently closed",
                        "status_code": status.HTTP_400_BAD_REQUEST
                        }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("An error occurred:", e)
                return Response({
                    "status": 0,
                    "errors": "An error occurred while checking date range",
                    "status_code": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST)
            validate_paper = validate_submission(data['paperupload'])
            if validate_paper == False:
                return Response({
                        "status": 0,
                        "errors": "Invalid file extension, only '.pdf' and '.pptx' files are allowed",
                        "status code": 415},status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            if validate_paper:
                data['paperupload'] = uploadPaper(request.FILES['paperupload'], request, PAPER_SUBMISSION_DIR, userId, trackId, topicId)                
            data['created_on'] = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
            serializer = SubmissionSerializer(data = data)
            serializer.is_valid(raise_exception=True)
            sub = serializer.save()
            CreateSubmissionId(sub.pk, topicId, trackId)
            return Response({"status": 0, "message": "Submission Successfull",
                            "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
            # elif abs.status == "Rejected":
            #     return Response({
            #         "errors": "Abstract has been rejected. Further submissions are not possible.",
            #         "status_code": status.HTTP_400_BAD_REQUEST
            #     }, status=status.HTTP_400_BAD_REQUEST)
            # else :
            #     return Response({
            #         "errors": "Abstract yet to be reviewed.",
            #         "status_code": status.HTTP_400_BAD_REQUEST
            #     }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_description= "To show all submissions in database",
        responses={200: submissions_response_schema}
    )
    @api_view(['get'])
    def ShowAllSubmissionsView(request):
        try:
            sub = Submission.objects.all()
            serializer = ShowSubmissionSerializer(sub, many = True)
            list = []
            for data in serializer.data:
                try:
                    data['paperupload'] = env("BASE_URL") + PAPER_SUBMISSION_DIR + data['paperupload']       
                except :
                    pass
                list.append(data)
            return Response({"status": 0, "data": list,"message": "Successfully Fetched the submissions",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='post',
        operation_description= "To show submissions by their id",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Submission ID')
            },
            required=['id']
        ),
        responses={200: submissions_response_schema}
    )
    @api_view(['post'])
    def ShowSubmissionByIDView(request):
        try:
            try:
                subId = request.data['id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sub = Submission.objects.get(id = subId)
            except Submission.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            serializer = ShowSubmissionSerializer(sub)
            data = serializer.data
            participant_details = []
            for userId in data['participants']:
                try:
                    user = AuthUser.objects.get(id = userId)
                except AuthUser.DoesNotExist:
                    return Response({"status": 0, "errors": "User Not Found",
                                    "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
                decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                participant_details.append(participant)
            data['participants'] = participant_details
            try:
                presentation = ConferencePresentation.objects.get(submission_id = subId)
                ser = ShowSelectedTimeslotSerializer(presentation)
                data2 = ser.data
                confirmed_participant_details = []
                for userId in data2['confirmed_participants']:
                    user = AuthUser.objects.get(id = userId)
                    decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                    confirmed_participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                    confirmed_participant_details.append(confirmed_participant)
                data['confirmed_participants'] = confirmed_participant_details
                data['timeslot_id'] = data2['timeslot_id']
            except:
                data['confirmed_participants'] = []
                data['timeslot_id'] = None
            try:
                data['paperupload'] = env("BASE_URL") + PAPER_SUBMISSION_DIR + data['paperupload'] 
            except :
                pass
            return Response({"status": 0, "data": data,"message": "Successfully Fetched the submission",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='post',
        operation_description= "To show submissions by user id",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID')
            },
            required=['user_id']
        ),
        responses={200: submissions_response_schema}
    )    
    @api_view(['post'])
    def ShowSubmissionByUserIDView(request):
        try:
            try:
                userId = request.data['user_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                user = AuthUser.objects.get(id = userId)
            except AuthUser.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                sub = Submission.objects.filter(user_id = userId)
            except Submission.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            serializer = ShowSubmissionSerializer(sub, many=True)
            data = serializer.data
            list = []
            for data in serializer.data:
                try:
                    data['paperupload'] = env("BASE_URL") + PAPER_SUBMISSION_DIR + data['paperupload']     
                    try:
                        conf = Event.objects.get(id = data['event_id'])
                    except Event.DoesNotExist:
                        return Response({"status": 0,  "errors": "Event Not Found",
                                        "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
                    data['conference_name'] = conf.name  
                except :
                    pass
                list.append(data)
            return Response({"status": 0, "data": list,"message": "Successfully Fetched the submission",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='post',
        operation_description= "To show all submissions for an event",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID')
            },
            required=['event_id']
        ),
        responses={200: submissions_response_schema}
    )   
    @api_view(['post'])
    def ShowSubmissionByEventIDView(request):
        try:
            try:
                eventId = request.data['event_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                sub = Submission.objects.filter(event_id = eventId)
            except Submission.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            serializer = ShowSubmissionSerializer(sub, many=True)
            ser_data = serializer.data
            list_data = []
            for data in ser_data:
                try:
                    participant_details = []
                    for userId in data['participants']:
                        user = AuthUser.objects.get(id = userId)
                        decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                        participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                        participant_details.append(participant)
                    data['participants'] = participant_details
                    try:
                        presentation = ConferencePresentation.objects.get(submission_id = data['id'])
                        ser = ShowSelectedTimeslotSerializer(presentation)
                        data2 = ser.data
                        confirmed_participant_details = []
                        for userId in data2['confirmed_participants']:
                            user = AuthUser.objects.get(id = userId)
                            decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                            confirmed_participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                            confirmed_participant_details.append(confirmed_participant)
                        data['confirmed_participants'] = confirmed_participant_details
                        data['timeslot_id'] = data2['timeslot_id']
                    except:
                        data['confirmed_participants'] = []
                        data['timeslot_id'] = None
                    data['paperupload'] = env("BASE_URL") + PAPER_SUBMISSION_DIR + data['paperupload'] 
                except :
                    pass
                list_data.append(data)
            return Response({"status": 0, "data": list_data,"message": "Successfully Fetched the submission",
                                "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='patch',
        operation_description= "To update details of an existing submission",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Submission ID'),
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the submission'),
                'abstract': openapi.Schema(type=openapi.TYPE_STRING, description='Abstract of the submission'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the submission'),
                'paperupload': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='List of paper uploads')
            },
            required=['id', 'event_id']
        ),
        responses={200: generic_response_schema}
    )   
    @api_view(['patch'])
    def UpdateSubmissionView(request):
        try:
            data=request.data.copy()
            try:
                subID = request.data['id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sub=Submission.objects.filter(id = subID).first()
            except Submission.DoesNotExist :
                return Response({"status": 0, "errors": [], "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if "paperupload" in data:
                validate_sub = validate_submission(data['paperupload'])
                if validate_sub == False:
                    return Response({
                            "status": 0,
                            "errors": "Invalid file extention, only '.pdf' and '.pptx' are allowed",
                            "status_code": 415
                            },status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
                if validate_sub:
                    data['paperupload'] = uploadPaper(request.FILES['paperupload'], request, PAPER_SUBMISSION_DIR, sub.user_id.id, sub.track_id.id, sub.topic_id.id)
                    print("paper", data['paperupload'])
                # paperuploads = request.FILES.getlist('paperupload')
                # if not paperuploads:
                #     return Response({"status": 0, "errors": "No files uploaded",
                #              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        
                # paperupload_list = []
                # for paperupload in paperuploads:
                #     validate_paper = validate_submission(paperupload)
                #     if validate_paper == False:
                #         return Response({
                #         "status": 0,
                #         "errors": "Invalid file extension, only '.pdf' and '.pptx' files are allowed",
                #         "status code": 415},status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
                #     uploaded_paper = uploadPaper(paperupload, request, PAPER_SUBMISSION_DIR, str(sub.user_id.id))
                #     print(uploaded_paper)
                #     paperupload_list.append(uploaded_paper)
        
                # data['paperupload'] = json.dumps(paperupload_list)
            eventId = sub.event_id.id
            print("eventid", eventId)
            data['updated_on'] = date.today()
            obj = Event.objects.filter(id = eventId).first()
            start_date = obj.start_date
            end_date = obj.end_date
            print("testcdsjb")
            try:
                if isDateinRange(start_date, end_date, data['updated_on']):
                    print("Date is within the range")
                    
                else:
                    print("Date is not within the range")
                    return Response({
                        "status": 0,
                        "errors": "Submissions are now closed",
                        "status_code": status.HTTP_400_BAD_REQUEST
                        }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("An error occurred:", e)
                return Response({
                    "status": 0,
                    "errors": "An error occurred while checking date range",
                    "status_code": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            data['updated_on'] = datetime.now(tz=ZoneInfo("Asia/Kolkata"))   
            
            serializer = UpdateSubmissionSerializer(sub, data = data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"status": 0, "message": "Successfully Updated the Submission",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#==================================================CRITERIA==================================================

class EventCriteria(GenericAPIView):

    @api_view(['post'])
    def CreateCriteriaView(request):
        try:
            data = request.data
            try:
                event = Event.objects.get(id = data['event_id'])
            except Event.DoesNotExist:
                return Response({"status": 0,  "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            serializer = CreateCriteriaSerializer(event, data=data)
            if not serializer.is_valid():
                error = serializer.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            serializer.save()
            return Response({"status": 0, "message": "Criteria created successfully.",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     # try:
    #         data = request.data.copy()
    #         try:
    #             data['event_id']
    #             data['criteria'] = json.dumps(data['criteria'])
    #         except KeyError as e:
    #             return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
    #                           "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #         try:
    #             event = Event.objects.get(id = data['event_id'])
    #         except Event.DoesNotExist:
    #             return Response({"status": 0, "errors": [], "errors": "Event Not Found",
    #                               "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
    #         data['updated_on'] = datetime.now()
    #         print("test")
    #         ser = CreateCriteriaSerializer(event, data=data)
    #         print("test1")
    #         if not ser.is_valid():
    #             error = ser.errors
    #             formatted_errors = {key: str(value[0]) for key, value in error.items()}
    #             raise serializers.ValidationError({
    #                 "errors": formatted_errors
    #             })            
    #         ser.save()
    #         return Response({"status": 0, "data": data,"message": "Successfully created the parameters",
    #                           "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    #     # except (TypeError, ValueError, NameError):
    #     #     return Response({"status": 0, "errors": "Something went wrong",
    #     #                       "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
    @swagger_auto_schema(
        method='post',
        operation_description= "To show the criteria created and their total maximum marks",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID')
            },
            required=['event_id']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status code'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
                            'criteria': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT), description='Criteria list'),
                            'total_max_marks': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total score')
                        }
                    ),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
                }
            ),
        }
    )
    @api_view(['post'])
    def ShowCriteriaByEventIdView(request):
        try:
            try:
                eventId = request.data['event_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ShowCriteriaSerializer(event)
            data = serializer.data
            data['criteria'] = json.loads(data['criteria'])
            return Response({"status": 0, "data": data,"message": "Successfully Fetched the criteria",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#=================================================REVIEW============================================

class SubmissionReview(GenericAPIView):

    @swagger_auto_schema(
        method='post',
        operation_description= "To create feedback, rating and score the criteria given in event criteria for a submission",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'submission_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Submission ID'),
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description='Rating between 1 to 5'),
                'feedback': openapi.Schema(type=openapi.TYPE_STRING, description='Feedback for the submission'),
                'criteria': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT), description="Criteria list {'criteria_name' : ' ', 'score' : ' '} "),
                'reviewed_by': openapi.Schema(type=openapi.TYPE_INTEGER, description='Reviewer ID'),
            },
            required=['submission_id', 'rating', 'feedback', 'criteria','reviewed_by']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status code'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Created review data'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
                }
            ),
        }
    )
    @api_view(['post'])
    def CreateReviewView(request):
        try:
            data = request.data.copy()
            try:
                userId = data['user_id']
                subId = data['submission_id']
                data['rating']
                data['feedback']
                data['criteria'] = json.dumps(data['criteria'])
                data['reviewed_by']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if ReviewSubmission.objects.filter(user_id=userId, submission_id = subId, reviewed_by = data['reviewed_by']).exists():
                return Response({
                    "errors": "You have already reviewed this submission",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            if validate_rating(data['rating']) == True:
                pass
            else:
                return Response({"status": 0, "errors": "Rating should be an integer between 1 to 5",
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = AuthUser.objects.get(id = userId)
            except AuthUser.DoesNotExist:
                 return Response({"status": 0, "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                sub = Submission.objects.get(id = subId)
            except Submission.DoesNotExist:
                 return Response({"status": 0, "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            eventId = sub.event_id.id
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                rev = Reviewer.objects.get(id = data['reviewed_by'])
            except Reviewer.DoesNotExist:
                return Response({"status": 0, "errors": "Reviewer Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            review_criteria_list = json.loads(data['criteria'])
            event_criteria_list = json.loads(event.criteria)
            event_criteria_dict = {}
            data['total_marks'] = 0
            for item in event_criteria_list:
                event_criteria_dict[item["criteria_name"]] = item["score"]
            for review_criterion in review_criteria_list:
                criteria_name = review_criterion['criteria_name']
                score = int(review_criterion['score'])
                data['total_marks'] = data['total_marks'] + score
                max_score = int(event_criteria_dict.get(criteria_name, 0))
                # review_criterion['max_score'] = max_score
                if score > max_score:
                    return Response({"status": 0, "errors": "Score for "+criteria_name+" should not exceed "+str(max_score),
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            data['criteria']=json.dumps(review_criteria_list)
            data['status'] = "Reviewed"
            statser = SubmissionStatusSerializer(sub , data = data)
            if not statser.is_valid():
                error = statser.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            statser.save()
            ser = CreateReviewSerializer(data = data)
            if not ser.is_valid():
                error = ser.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            ser.save()
            return Response({"status": 0, "data": data,"message": "Successfully reviewed the submission",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

    @swagger_auto_schema(
        method='post',
        operation_description= "To show all the details of submission including review details and user details",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'submission_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Submission ID')
            },
            required=['submission_id']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status code'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'submission_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Submission ID'),
                            'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description='Rating'),
                            'feedback': openapi.Schema(type=openapi.TYPE_STRING, description='Feedback'),
                            'criteria': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT), description='Criteria list'),
                            'total_marks': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total marks')
                        }
                    ),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message')
                }
            ),
        }
    )
    @api_view(['post'])
    def ShowReviewBySubmissionIdView(request):
        try:
            try:
                subId = request.data['submission_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sub = Submission.objects.get(id = subId)
            except Submission.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            eventId = sub.event_id.id
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            userId = sub.user_id.id
            try:
                user = AuthUser.objects.get(id = userId)
            except AuthUser.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                track = Track.objects.get(id = sub.track_id.id)
            except Track.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Track Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                topic = Topic.objects.get(id = sub.topic_id.id)
            except Topic.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Topic Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            rev = ReviewSubmission.objects.get(submission_id = subId)
            serializer = ShowReviewSerializer(rev)
            data = serializer.data
            decrypt = data_decrypt(username = user.username, mob = user.mobileno, mail = user.email)
            data['username'] = decrypt['username']  
            data['user_mobile'] = decrypt['mob']
            data['user_mail'] = decrypt['mail']
            data['event'] = event.name
            data['track'] = track.track_name
            data['topic'] = topic.topic
            data['criteria'] = json.loads(data['criteria'])
            data["paperupload"] = env("BASE_URL") + PAPER_SUBMISSION_DIR + str(userId) + "/" + sub.paperupload
            data['title'] = sub.title
            data['description'] = sub.description
            return Response({"status": 0, "data": data,"message": "Successfully Fetched the review",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#====================================================ORGANIZER===========================================

class OrganizerCheck(GenericAPIView):

    @swagger_auto_schema(
        method='post',
        operation_description= "To approve or reject a submission",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'submission_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Submission ID'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status to set ("True" or "1" for approval, otherwise rejection)')
            },
            required=['submission_id', 'status']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='Status code'),
                    # 'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='Empty list'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Submission status message')
                }
            ),
        }
    )
    @api_view(['post'])
    def AppOrRejView(request):
        try:
            data = request.data.copy()
            try:
                subId = data['submission_id']
                stat = data['status'] 
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sub = Submission.objects.get(id = subId)
            except Submission.DoesNotExist:
                return Response({"status": 0, "errors": [], "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if stat == "True" or stat == "1":
                data['status'] = "Approved"
                ser = SubmissionStatusSerializer(sub, data = data)
            else:
                data['status'] = "Rejected"
                ser = SubmissionStatusSerializer(sub, data = data)
            if not ser.is_valid():
                error = ser.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            ser.save()
            return Response({"status": 0, "data": [] ,"message": "Submission " + sub.status ,
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='post',
        operation_description= "To create ranking list for an event",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
                'position': openapi.Schema(type=openapi.TYPE_OBJECT, description="Rankings list - {'user'' : ' ','position':' ','prize':' '}")
            },
            required=['event_id', 'position']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='Positions'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Positions and prize money updated')
                }
            ),
        }
    )
    @api_view(['post'])
    def CreatePositionView(request):
        try:
            data = {}
            try:
                eventId = request.data['event_id']
                data['position'] = json.dumps(request.data['position'])
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({ "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = CreateEventRankSerializer(event, data = data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({ "data": json.loads(data['position']) ,"message": "Positions and prize money updated",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='post',
        operation_description= "To show the ranking list for an event",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID')
            },
            required=['event_id']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            # 'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Event ID'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Event name'),
                            'position': openapi.Schema(type=openapi.TYPE_OBJECT, description='Positions and prize money')
                        }
                    ),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Successfully fetched the rankings')
                }
            ),
        }
    )   
    @api_view(['post'])
    def ShowEventRankingsView(request):
        try:
            try:
                eventId = request.data['event_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({ "errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = ShowEventRankSerializer(event)
            data = ser.data
            data['position'] = json.loads(data['position'])
            return Response({ "data": data ,"message": "Successfully fetched the rankings",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def CreateCertificateView(request):
        try:
            data = request.data.copy()
            try:
                subId= data['submission_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sub = Submission.objects.get(id = subId)
            except Submission.DoesNotExist:
                return Response({"errors": [], "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            eventId = sub.event_id.id
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            userId = sub.user_id.id
            try:
                user = AuthUser.objects.get(id = userId)
            except AuthUser.DoesNotExist:
                return Response({"errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                topic = Topic.objects.get(id = sub.topic_id.id)
            except Topic.DoesNotExist:
                return Response({"errors": [], "errors": "Topic Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                track = Track.objects.get(id = sub.track_id.id)
            except Track.DoesNotExist:
                return Response({"errors": [], "errors": "Track Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            decrypt = data_decrypt(first = user.first_name, last = user.last_name)
            name = str(decrypt['first'] + " " + decrypt['last'])
            data['certificate'] = make_certificates(name,topic.topic,event.name,track.track_name, CERTIFICATE_DIR)
            ser= CreateCertificateSerializer(data = data)
            ser.is_valid(raise_exception=True)
            cert = ser.save()
            CreateCertificateId(cert.pk , eventId)
            return Response({ "data": data ,"message": "Successfully created the certificate",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @api_view(['post'])
    def AssignSpeakerView(request):
        try:
            try:
                eventId = request.data['event_id']
                userId = request.data['user_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            speakerlist = []
            print(userId)
            for t in userId:
                if t != ',':
                    try:
                        user = AuthUser.objects.get(id = t)
                    except AuthUser.DoesNotExist:
                        return Response({"errors": [], "errors": "User Not Found",
                                        "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
                    decrypt = data_decrypt(first = user.first_name, last = user.last_name)
                    name = decrypt['first']  + decrypt['last']
                    speakerlist.append(name)
            data = {}
            data['speaker'] = json.dumps(speakerlist)
            ser = CreateSpeakerSerializer(event, data = data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({ "data": data ,"message": "Successfully added the speakers",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
        
    @api_view(['post'])
    def GetSpeakerView(request):
        try:
            try:
                eventId = request.data['event_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = ShowSpeakerSerializer(event)
            data = ser.data
            data['speaker'] = json.loads(data['speaker'])
            return Response({ "data": data ,"message": "Successfully fetched the speakers list",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#=====================================================ABSTRACT==================================================

class SubmitAbstract(GenericAPIView):
    
    @api_view(['post'])
    def CreateAbstractView(request):
        try:
            data = request.data.copy()
            try:
                userId = data['user_id']
                data['abstract']
                eventId = data['event_id']
                trackId = data['track_id']
                topicId = data['topic_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            data['created_on'] = date.today()
            obj = Event.objects.filter(id = data['event_id']).first()
            start_date = obj.abs_start.date()
            end_date = obj.abs_end.date()
            try:
                if isDateinRange(start_date, end_date, data['created_on']):
                    print("Date is within the range")
                    data['status'] = "Submitted"
                else:
                    print("Date is not within the range")
                    return Response({
                        "status": 0,
                        "errors": "Abstract submissions are currently closed",
                        "status_code": status.HTTP_400_BAD_REQUEST
                        }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("An error occurred:", e)
                return Response({
                    "status": 0,
                    "errors": "An error occurred while checking date range",
                    "status_code": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST)
            data['created_on'] = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
            try:
                user = AuthUser.objects.get(id = userId)
            except AuthUser.DoesNotExist:
                return Response({"errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                topic = Topic.objects.get(id = topicId)
            except Topic.DoesNotExist:
                return Response({"errors": [], "errors": "Topic Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                track = Track.objects.get(id = trackId)
            except Track.DoesNotExist:
                return Response({"errors": [], "errors": "Track Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if Abstract.objects.filter(user_id=userId,event_id=eventId,track_id=trackId,topic_id=topicId).exists():
                return Response({
                    "errors" : "You already submitted abstract for the same topic in this conference",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            validate_abs = validate_submission(data['abstract'])
            if validate_abs == False:
                return Response({
                        "status": 0,
                        "errors": "Invalid file extension, only '.pdf' and '.pptx' files are allowed",
                        "status code": 415},status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            if validate_abs:
                data['abstract'] = uploadAbstract(request.FILES['abstract'], request, ABSTRACT_SUBMISSION_DIR, userId, trackId, topicId)
            data['status'] = "Abstract Submitted"
            ser = CreateAbstractSerializer(data = data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({ "data": data ,"message": "Successfully submitted the abstract",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['get'])
    def GetAllAbstractView(request):
        try:
            abs = Abstract.objects.all()
            list = []
            ser = ShowAbstractSerializer(abs, many = True)
            for data in ser.data:
                try:
                    data['abstract'] = env("BASE_URL") + ABSTRACT_SUBMISSION_DIR + data['abstract']       
                except :
                    pass
                list.append(data)
            return Response({ "data": list ,"message": "Successfully fetched the abstracts",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @api_view(['post'])
    def GetAbstractByUserIdView(request):
        try:
            try:
                userId = request.data['user_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                user = AuthUser.objects.get(id = userId)
            except AuthUser.DoesNotExist:
                return Response({"errors": [], "errors": "User Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            abs = Abstract.objects.filter(user_id = userId)
            list = []
            ser = ShowAbstractSerializer(abs, many = True)
            for data in ser.data:
                try:
                    data['abstract'] = env("BASE_URL") + ABSTRACT_SUBMISSION_DIR + data['abstract']       
                except :
                    pass
                list.append(data)
            return Response({ "data": list ,"message": "Successfully fetched the abstracts",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def GetAbstractByIdView(request):
        try:
            try:
                absId = request.data['id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                abs = Abstract.objects.get(id = absId)
            except Abstract.DoesNotExist:
                return Response({"errors": [], "errors": "Abstract Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = ShowAbstractSerializer(abs)
            data = ser.data
            try:
                data['abstract'] = env("BASE_URL") + ABSTRACT_SUBMISSION_DIR + data['abstract']       
            except :
                pass
            return Response({ "data": data ,"message": "Successfully fetched the abstracts",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def GetAbstractByEventIdView(request):
        try:
            try:
                eventId = request.data['event_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            abs = Abstract.objects.filter(event_id = eventId)
            list = []
            ser = ShowAbstractSerializer(abs, many = True)
            for data in ser.data:
                try:
                    data['abstract'] = env("BASE_URL") + ABSTRACT_SUBMISSION_DIR + data['abstract']       
                except :
                    pass
                list.append(data)
            return Response({ "data": list ,"message": "Successfully fetched the abstracts",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @api_view(['patch'])
    def UpdateAbstractView(request):
        try:
            data = request.data.copy()
            try:
                absId = data['id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                abs = Abstract.objects.get(id = absId)
            except Abstract.DoesNotExist:
                return Response({"errors": [], "errors": "Abstract Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            data['updated_on'] = date.today()
            try:
                event = Event.objects.get(id = abs.event_id.pk)
            except Event.DoesNotExist:
                return Response({"errors": [], "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            obj = Event.objects.filter(id = abs.event_id.pk).first()
            start_date = obj.abs_start.date()
            end_date = obj.abs_end.date()
            try:
                if isDateinRange(start_date, end_date, data['updated_on']):
                    print("Date is within the range")
                    # data['status'] = "Submitted"
                else:
                    print("Date is not within the range")
                    return Response({
                        "status": 0,
                        "errors": "Abstract submissions are currently closed",
                        "status_code": status.HTTP_400_BAD_REQUEST
                        }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("An error occurred:", e)
                return Response({
                    "status": 0,
                    "errors": "An error occurred while checking date range",
                    "status_code": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST)
            data['updated_on'] = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
            if 'abstract' in data:
                validate_abs = validate_submission(data['abstract'])
                if validate_abs == False:
                    return Response({
                            "status": 0,
                            "errors": "Invalid file extension, only '.pdf' and '.pptx' files are allowed",
                            "status code": 415},status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
                if validate_abs:
                    data['abstract'] = uploadAbstract(request.FILES['abstract'], request, ABSTRACT_SUBMISSION_DIR, abs.user_id.pk, abs.track_id.pk, abs.topic_id.pk)
            ser = UpdateAbstractSerializer(abs, data = data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({ "data": data ,"message": "Successfully updated the abstract",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ReviewAbstract(GenericAPIView):

    def post(self, request):
        try:
            data = request.data.copy()
            try:
                absId = data['abstract_id']
                revId = data['reviewed_by']
                data['remarks']
                data['status']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                abs = Abstract.objects.get(id = absId)
            except Abstract.DoesNotExist:
                return Response({"errors": [], "errors": "Abstract Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                rev = Reviewer.objects.get(id = revId)
            except Reviewer.DoesNotExist:
                return Response({"errors": [], "errors": "Reviewer Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = ReviewAbstractSerializer(abs, data=data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({ "data": data ,"message": "Successfully reviewed the abstract",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def GetAbstractReview(request):
        try:
            try:
                absId = request.data['abstract_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                abs = Abstract.objects.get(id = absId)
            except Abstract.DoesNotExist:
                return Response({"errors": [], "errors": "Abstract Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = ShowAbstractReviewSerializer(abs)
            data = ser.data
            try:
                data['abstract'] = env("BASE_URL") + ABSTRACT_SUBMISSION_DIR + data['abstract']       
            except :
                pass
            return Response({ "data": data ,"message": "Successfully fetched the abstracts",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#===================================================TIMESLOTS================================================

class ConferenceTimeslot(GenericAPIView):

    @api_view(['post'])
    def CreateTimeslot(request):
        try:
            data = request.data.copy()
            try:
                eventId = data['event_id']
                data['timeslots']
                # data['date']
                # data['start_time']
                # data['end_time']
                # data['mode']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"status": 0, "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            # data['created_by'] = event.created_by.pk
            for slot in data['timeslots']:
                data['start_time'] = datetime.strptime(slot['start'], '%Y-%m-%d %H:%M:%S')
                data['end_time'] = datetime.strptime(slot['end'], '%Y-%m-%d %H:%M:%S')
                data['mode'] = slot['mode']
                ser = CreateTimeslotSerializer(data = data)
                if not ser.is_valid():
                    error = ser.errors
                    formatted_errors = {key: str(value[0]) for key, value in error.items()}
                    raise serializers.ValidationError({
                        "errors": formatted_errors
                    })
                ser.save()
            return Response({ "data": [] ,"message": "Successfully created the timeslots",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self,request):
        try:
            list = []
            slot = TimeSlot.objects.all()
            ser = ShowTimeslotSerializer(slot, many = True)
            for data in ser.data:
                list.append(data)
            return Response({ "data": list ,"message": "Successfully fetched the timeslots",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def ShowTimeslotByEventId(request):
        try:
            try:
                eventId = request.data['event_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({ "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            list = []
            slot = TimeSlot.objects.filter(event_id = eventId)
            ser = ShowTimeslotSerializer(slot, many = True)
            for data in ser.data:
                list.append(data)
            return Response({ "data": list ,"message": "Successfully fetched the timeslots",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def UpdateTimeslotView(request):
        try:
            data = request.data.copy()
            try:
                slotId = data['timeslot_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                                "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                slot = TimeSlot.objects.get(id = slotId)
            except TimeSlot.DoesNotExist:
                return Response({ "errors": "Timeslot Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            data['start_time'] = datetime.strptime(data['start'], '%Y-%m-%d %H:%M:%S')
            data['end_time'] = datetime.strptime(data['end'], '%Y-%m-%d %H:%M:%S')
            data['mode'] = data['mode'].lower()
            ser = UpdateTimeslotSerializer(slot, data = data)
            if not ser.is_valid():
                error = ser.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            ser.save()
            return Response({ "data": [] ,"message": "Successfully updated the timeslot",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @api_view(['post'])
    def AddTimeslotView(request):
        try:
            data = request.data.copy()
            try:
                eventId = data['event_id']
                data['start']
                data['end']
                data['mode']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                                "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({"errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            data['start_time'] = datetime.strptime(data['start'], '%Y-%m-%d %H:%M')
            data['end_time'] = datetime.strptime(data['end'], '%Y-%m-%d %H:%M')
            if data['start_time'] >= data['end_time']:
                return Response({ "errors": "Start time should not be greater than or equal to end time",
                                "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            data['mode'] = data['mode'].lower()
            if TimeSlot.objects.filter(event_id=eventId,start_time=data['start_time'],end_time=data['end_time'],mode=data['mode']).exists():
                return Response({ "errors": "Timeslot with same data already exists for this event",
                                "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            ser = CreateTimeslotSerializer( data = data)
            if not ser.is_valid():
                error = ser.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            ser.save()
            return Response({ "data": [] ,"message": "Successfully created the timeslot",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def DeleteTimeslotView(request):
        try:
            try:
                slotID = request.data['timeslot_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                slot = TimeSlot.objects.get(id=slotID)
            except TimeSlot.DoesNotExist:
                return Response({
                "status": 0,
                "errors": "Timeslot not found.",
                "status_code": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)
            slot.delete()
            return Response({
            "status": 0,
            "message": "Successfully deleted the slot.",
            "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({"status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def SelectTimeslotView(request):
        try:
            data = request.data
            try:
                subId = data['submission_id']
                slotId = data['timeslot_id']
                data['confirmed_participants']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            try:
                sub = Submission.objects.get(id = subId)
            except Submission.DoesNotExist:
                return Response({"status": 0, "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                timeslot = TimeSlot.objects.get(id = slotId)
            except TimeSlot.DoesNotExist:
                return Response({"status": 0, "errors": "Timeslot Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if data['confirmed_participants'] == []:
                return Response({"status": 0, "errors": "Select atleast one participant.",
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            # if ConferencePresentation.objects.filter(submission_id = subId).exists():
            #     return Response({"status": 0, "errors": "Timeslot has already been selected for this submission.",
            #                       "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            # if ConferencePresentation.objects.filter(timeslot_id = slotId).exists():
            #     return Response({"status": 0, "errors": "Timeslot not available. Choose a different timeslot.",
            #                       "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            if ConferencePresentation.objects.filter(submission_id = subId).exists():
                presentation = ConferencePresentation.objects.get(submission_id = subId)
                data['updated_on'] = datetime.now()
                ser = EditSelectedTimeslotSerializer(presentation, data = data)
            else:
                data['created_on'] = datetime.now()
                ser = SelectTimeslotSerializer(data = data)
            if not ser.is_valid():
                error = ser.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            ser.save()
            return Response({ "status": 1, "data": data ,"message": "Successfully selected the timeslot",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "status": 0, "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @api_view(['post'])
    def GetSelectedSlotById(request):
        try:
            try:
                presentation_id = request.data['id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            try:
                presentation = ConferencePresentation.objects.get(id = presentation_id)
            except ConferencePresentation.DoesNotExist:
                return Response({"status": 0, "errors": "Timeslot has not been selected",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = ShowSelectedTimeslotSerializer(presentation)
            data = ser.data
            participant_details = []
            for userId in data['confirmed_participants']:
                try:
                    user = AuthUser.objects.get(id = userId)
                except AuthUser.DoesNotExist:
                    return Response({"status": 0, "errors": "User Not Found",
                                    "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
                decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                participant_details.append(participant)
            data['confirmed_participants'] = participant_details
            return Response({ "data": data ,"message": "Successfully fetched the selected timeslot",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @api_view(['post'])
    def GetSelectedSlotBySubmissionId(request):
        try:
            try:
                sub_id = request.data['submission_id']
            except KeyError as e:
                return Response({"status": 0, "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            try:
                presentation = ConferencePresentation.objects.get(submission_id = sub_id)
            except ConferencePresentation.DoesNotExist:
                return Response({"status": 0, "errors": "Timeslot has not been selected",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            ser = ShowSelectedTimeslotSerializer(presentation)
            data = ser.data
            participant_details = []
            for userId in data['confirmed_participants']:
                try:
                    user = AuthUser.objects.get(id = userId)
                except AuthUser.DoesNotExist:
                    return Response({"status": 0, "errors": "User Not Found",
                                    "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
                decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                participant_details.append(participant)
            data['confirmed_participants'] = participant_details
            return Response({ "data": data ,"message": "Successfully fetched the selected timeslot",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @api_view(['post'])
    def GetPresentationConfirmationDataView(request):
        try:
            data = request.data
            try:
                eventId = data['event_id']
                submissionId = data['submission_id']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                              "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                event = Event.objects.get(id = eventId)
            except Event.DoesNotExist:
                return Response({ "errors": "Event Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            try:
                submission = Submission.objects.get(id = submissionId)
            except Submission.DoesNotExist:
                return Response({ "errors": "Submission Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            # data = {}
            slot = TimeSlot.objects.filter(event_id = eventId)
            ser = ShowTimeslotSerializer(slot, many = True)
            data['timeslots'] = ser.data
            participants = submission.participants
            participant_details = []
            for userId in participants:
                user = AuthUser.objects.get(id = userId)
                decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                participant_details.append(participant)
            data['participants'] = participant_details
            try:
                presentation = ConferencePresentation.objects.get(submission_id = submissionId)
                ser = ShowSelectedTimeslotSerializer(presentation)
                data2 = ser.data
                confirmed_participant_details = []
                for userId in data2['confirmed_participants']:
                    user = AuthUser.objects.get(id = userId)
                    decrypt = data_decrypt(first = user.first_name, last=user.last_name, mail=user.email)
                    confirmed_participant = {"user_id":userId, "first_name":decrypt['first'], "last_name":decrypt['last'], "email":decrypt['mail']}
                    confirmed_participant_details.append(confirmed_participant)
                data['confirmed_participants'] = confirmed_participant_details
                selected_timeslot = TimeSlot.objects.get(id=data2['timeslot_id'])
                serializer = ShowTimeslotSerializer(selected_timeslot)
                data['selected_timeslot'] = serializer.data
            except:
                data['confirmed_participants'] = []
                data['selected_timeslot'] = None
            return Response({ "data": data ,"message": "Successfully fetched the timeslots and participants details.",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#=================================================RESULT_DECLARATION======================================

class ResultDeclaration(GenericAPIView):

    @api_view(['post'])
    def CreateResultDeclarationView(request):
        try:
            data = request.data
            try:
                submissionId = data['submission_id']
                data['status'] = data['status'].lower()
                data['prize']
            except KeyError as e:
                return Response({ "errors": f"Necessary Field {e} is not available in the request",
                                "status_code": status.HTTP_204_NO_CONTENT}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                presentation = ConferencePresentation.objects.get(submission_id = submissionId)
            except ConferencePresentation.DoesNotExist:
                return Response({ "errors": "Conference presentation Not Found",
                                  "status_code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            data['updated_on'] = datetime.now()
            if 'position' not in data:
                data['position'] = None
            ser = CreateResultSerializer(presentation, data = data)
            if not ser.is_valid():
                error = ser.errors
                formatted_errors = {key: str(value[0]) for key, value in error.items()}
                raise serializers.ValidationError({
                    "errors": formatted_errors
                })
            ser.save()
            return Response({ "data": [] ,"message": "Successfully created the result of the conference",
                              "status_code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, NameError):
            return Response({ "errors": "Something went wrong",
                              "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
            
            

        

            
