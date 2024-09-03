import os
import re
import magic
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator
from core.models import *
import zipfile




mobile_number = RegexValidator(r'^\d{10}$', 'Please enter valid mobile number.')
emailregex = RegexValidator(r'[^@]+@[^@]+\.[^@]+', "Please enter a valid email address")

#================================================LOGIN========================================================

class LoginSerializer(ModelSerializer):

    class Meta:
        model = AuthUser
        fields = ['first_name', 'last_name', 'mobileno', 'email', 'is_active', 'username', 'k_id', 'last_login', 'unique_id']

class LastloginSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthUser
        fields = ['last_login', 'unique_id']

class UserGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthUserGroups
        fields = "__all__"

class ShowUserSerializer(ModelSerializer):

    class Meta:
        model = AuthUser
        fields = ['id','first_name', 'last_name', 'mobileno', 'email', 'is_active', 'username', 'k_id', 'last_login', 'unique_id']

class CreateReviewerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reviewer
        fields = ['event_id', 'user_id']

# class ShowParticipantsSerializer(ModelSerializer):

#     class Meta:
#         model = AuthUser
#         fields = ['user_id', 'first_name', 'last_name', 'email']

#================================================CONFERENCE_MANAGEMENT========================================================

class CreateEventSerializer(ModelSerializer):

    orga_email = serializers.CharField(
        required=True,
        validators=[emailregex],
    )

    shortform = serializers.CharField(
        required = True,
        validators = [UniqueValidator(queryset=Event.objects.all())]
    )
    class Meta:
        model = Event
        fields = ['id','name', 'shortform', 'orga_email', 'start_date', 
                   'end_date', 'reg_link', 'event_color', 'logo', 'header_image',
                     'landing_text','is_public', "track_id",'created_by', 'created_on', 'updated_on']
    
    def validate_name(self,name):
        regex = re.compile('[@_!#$%^&*+\-*()<>?/\|}{~:]')
        # re.findall('[0-9]', name) or
        if regex.search(name) != None :
            raise serializers.ValidationError({
                    "Only alphabatic characters are allowed"
            })
        return name

class EventIDSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['event_id']

class ShowEventSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['id','event_id','name', 'shortform', 'orga_email', 'start_date', 
                   'end_date', 'reg_link', 'event_color', 'logo', 'header_image',
                     'landing_text','is_public', "track_id",'created_by', 'created_on', 'updated_on']

class UpdateEventSerializer(ModelSerializer):

    orga_email = serializers.CharField(
        required=False,
        validators=[emailregex],
    )
    
    class Meta:
        model = Event
        fields = ['id','name', 'orga_email', 'start_date', 
                   'end_date', 'reg_link', 'event_color', 'logo', 'header_image',
                     'landing_text','is_public', 'updated_on', 'track_id']
        extra_kwargs = {
            "name": {"required": False},
            "orga_email":{"required": False},
            "start_date":{"required": False},
            "end_date":{"required": False},
            "reg_link":{"required": False},
            "logo":{"required": False},
        }

def validate_img(pic):
        if type(pic) == str:
            if pic != "null":
                return False
        else:
            file_type = magic.from_buffer(pic.read(1024), mime=True)
            valid_filetype = ['image/jpeg', "image/png"]
            if file_type not in valid_filetype:
                raise serializers.ValidationError({
                "errors": "Invalid Filetype, '.jpg', '.jpeg' and '.png' are allowed"
                })
            
            filesize = pic.size
            megabyte_limit = 1
            valid_extensions = ['.jpg', '.jpeg', '.png']  

            ext = os.path.splitext(pic.name)[1]
        
            if ext.lower() not in valid_extensions:
                raise serializers.ValidationError({
                "errors": "Invalid Filetype, '.jpg', '.jpeg' and '.png' are allowed"
                })
        
            file_name, file_ext = os.path.splitext(pic.name)
            if os.path.splitext(file_name)[1]:
                raise serializers.ValidationError({
                "errors": "Invalid Filetype, '.jpg', '.jpeg' and '.png' are allowed"
                })
            elif filesize > megabyte_limit * 1024 * 1024:
                raise serializers.ValidationError({
                "errors": "File size should not exceed 1MB"
                })
            else :
                return  pic
            
class CreateEventRankSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['position']

class ShowEventRankSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['name', 'position']
#================================================TRACK_MANAGEMENT========================================================    

class CreateTrackSerializer(ModelSerializer):

    class Meta:
        model = Track
        fields = ['track_name',  "updated_on"]

    def validate_track_name(self,track_name):
        if re.search(r'[<>@]', track_name):
            raise serializers.ValidationError("The characters <, >, and @ are not allowed.")
        return track_name

class TrackIDSerializer(ModelSerializer):

    class Meta:
        model = Track
        fields = ['track_id']

class ShowTrackSerializer(ModelSerializer):

    class Meta:
        model = Track
        fields = ['id','track_name', 'track_id']

class UpdateTrackSerializer(ModelSerializer):

    class Meta:
        model = Track
        fields = ['track_name',  "updated_on"]
        extra_kwargs = {
            "track_name":{"required": False}
        }

    def validate_track_name(self,track_name):
        if re.search(r'[<>@]', track_name):
            raise serializers.ValidationError("The characters <, >, and @ are not allowed.")
        return track_name
    
#=========================================================TOPIC=======================================================

class CreateTopicSerializer(ModelSerializer):

    class Meta:
        model = Topic
        fields = ['id', 'trackid', 'topic']

    def validate_topic(self,topic):
        if re.search(r'[<>@]', topic):
            raise serializers.ValidationError("The characters <, >, and @ are not allowed.")
        return topic

class ShowTopicSerializer(ModelSerializer):

    class Meta:
        model = Topic
        fields = ['id', 'trackid', 'topic']

# class CreateTopicUnderTrackSerializer(ModelSerializer):
    
#     class Meta:
#         model = Topic
#         fields = ['track_id', 'topic_name']

#===================================================USER SUBMISSION======================================================

class SubmissionSerializer(ModelSerializer):


    class Meta:
        model = Submission
        fields = ['user_id', 'title', 'description', 'paperupload', 'status', 'created_on', 'event_id','track_id', 'topic_id','team_composition','participants']
        # extra_kwargs = {"status": {"required": False}}

    def validate_title(self,title):
        if re.search(r'[<>@]', title):
            raise serializers.ValidationError("The characters <, >, and @ are not allowed.")
        return title


class SubmissionIDSerializer(ModelSerializer):

    class Meta:
        model = Submission
        fields = ['submission_id']

class ShowSubmissionSerializer(ModelSerializer):
    track_id = ShowTrackSerializer()
    topic_id = ShowTopicSerializer()

    class Meta:
        model = Submission
        fields = "__all__"

class UpdateSubmissionSerializer(ModelSerializer):

    class Meta:
        model = Submission
        fields = ['id', 'title', 'description', 'paperupload', 'updated_on', 'track_id','topic_id']

    extra_kwargs = {
            "title": {"required": False},
            "abstract":{"required": False},
            "description":{"required": False},
            "paperupload":{"required": False},
            'track_id':{"required": False},
            'topic_id':{"required": False}
        }
    
    def validate_title(self,title):
        if re.search(r'[<>@]', title):
            raise serializers.ValidationError("The characters <, >, and @ are not allowed.")
        return title
    
class SubmissionStatusSerializer(ModelSerializer):

    class Meta:
        model = Submission
        fields = ['status']
    
#========================================================CRITERIA========================================================

class CreateCriteriaSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['criteria', 'updated_on']

    def validate_criteria(self,criteria):
        for crit in criteria:
            if re.search(r'[<>@]', crit['criteria_name']):
                raise serializers.ValidationError({"The characters <, > and @ are not allowed in criteria name."})
            if not crit['score'].isdigit():
                raise serializers.ValidationError({"Only integer values to provided for score."})
        return criteria

class ShowCriteriaSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['criteria', 'updated_on']



#========================================================REVIEW=============================================

class CreateReviewSerializer(ModelSerializer):

    class Meta:
        model = ReviewSubmission
        fields = ['user_id', 'submission_id', 'rating', 'criteria', 'feedback', 'total_marks','reviewed_by']
        

class ShowReviewSerializer(ModelSerializer):

    class Meta:
        model = ReviewSubmission
        fields = [ 'rating', 'criteria', 'feedback','total_marks','reviewed_by']

#==========================================sdfhbhc============================================

class CreateCertificateSerializer(ModelSerializer):

    class Meta:
        model = Certificate
        fields = ['certificate','submission_id']

class CreateCertificateIDSerializer(ModelSerializer):

    class Meta:
        model = Certificate
        fields = ['certificate_id']

class CreateSpeakerSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['speaker']

class ShowSpeakerSerializer(ModelSerializer):

    class Meta:
        model = Event
        fields = ['event_id', 'name', 'speaker']

#=======================================================ABSTRACT============================================

class CreateAbstractSerializer(ModelSerializer):

    class Meta:
        model = Abstract
        fields = ['abstract', 'user_id', 'created_on', 'event_id', 'topic_id', 'track_id','status','updated_on']

class ShowAbstractSerializer(ModelSerializer):

    class Meta:
        model = Abstract
        fields = [ 'user_id', 'event_id', 'track_id', 'topic_id','abstract', 'status', 'created_on', 'updated_on']

class UpdateAbstractSerializer(ModelSerializer):

    class Meta:
        model = Abstract
        fields = [ 'user_id', 'event_id', 'track_id', 'topic_id','abstract', 'updated_on']

class ReviewAbstractSerializer(ModelSerializer):

    class Meta:
        model = Abstract
        fields = ['reviewed_by', 'remarks', 'status']

class ShowAbstractReviewSerializer(ModelSerializer):

    class Meta:
        model = Abstract
        fields = "__all__"

#=======================================================TIMESLOTS=======================================

class CreateTimeslotSerializer(ModelSerializer):

    class Meta:
        model = TimeSlot
        fields = "__all__"

class ShowTimeslotSerializer(ModelSerializer):

    class Meta:
        model = TimeSlot
        fields = "__all__"

class UpdateTimeslotSerializer(ModelSerializer):

    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time', 'mode']

class SelectTimeslotSerializer(ModelSerializer):

    class Meta:
        model = ConferencePresentation
        fields = ['submission_id', 'timeslot_id', 'confirmed_participants','created_on']

class EditSelectedTimeslotSerializer(ModelSerializer):

    class Meta:
        model = ConferencePresentation
        fields = ['submission_id', 'timeslot_id', 'confirmed_participants','updated_on']

class ShowSelectedTimeslotSerializer(ModelSerializer):

    class Meta:
        model = ConferencePresentation
        fields = ['id', 'submission_id', 'timeslot_id', 'confirmed_participants','created_on','updated_on']

#+============================================RESULT_DECLARATION==========================================

class CreateResultSerializer(ModelSerializer):

    class Meta:
        model = ConferencePresentation
        fields = ["submission_id", "status","position","prize","updated_on"]
      


    

        



            
