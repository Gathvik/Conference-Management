from django.urls import path
from core.views import *

urlpatterns = [
#================================================Login========================================================

    path("", DefaultAPIView.as_view()),
    path("Login", IvpLogin.as_view(), name="ivplogin"),

#================================================USER_MANAGEMENT========================================================

    path("UserDetails", UserDetails.as_view(), name="userDetails"),
    path("AllUserDetails", AllUserDetails.as_view(), name="alluserdetails"),
    path("AssignRole", AssignRole.as_view(), name="assignrole"),
    path("AssignReviewer", AssignReviewer.as_view(), name="assignreviewer"),
    path("DeleteReviewer", DeleteReviewer.as_view(), name="deletereviewer"),

#================================================EVENT========================================================

    path("CreateEvent", EventView.CreateEventView, name="createEvent"),
    path("GetEventByID", EventView.ShowEventByIdView, name="showevent"),
    path("GetEventAll", EventView.ShowAllEventview, name="showallevent"),
    path("UpdateEvent", EventView.UpdateEventView, name="updateEvent"),
    path("ShowUpcomingEvents", EventView.ShowUpcomingEventView, name="showupcomingevent"),

#================================================EVENT_TRACK========================================================

    path("CreateTrack", TrackView.CreateTrackView, name="createtrack"),
    path("ShowTrackByID", TrackView.ShowTrackByIdView, name="showtrackbyid"),
    path("ShowAllTracks", TrackView.ShowAllTrackView, name="gettrackall"),
    path("UpdateTrack", TrackView.UpdateTrackView, name="updatetrack"),
    path("DeleteTopic", TrackView.DeleteTopicView, name="deletetopic"),

#================================================COUNT========================================================

    path("DataCounts", Count.as_view(), name="count"),

#=============================================USER SUBMISSION================================================    

    path("CheckUserRegistration", CheckUserRegistration.as_view(), name = "checkuserregistration"),
    path("CreateSubmission", UserSubmission.CreateSubmissionView, name="createsubmission"),
    path("ShowAllSubmissions", UserSubmission.ShowAllSubmissionsView, name="showallsubmissions"),
    path("UpdateSubmission", UserSubmission.UpdateSubmissionView, name="updatesubmission"),
    path("ShowSubmissionByID", UserSubmission.ShowSubmissionByIDView, name="showsubmissionbyid"),
    path("ShowSubmissionByUserId", UserSubmission.ShowSubmissionByUserIDView, name="showsubmissionbyuserid"),
    path("ShowSubmissionByEventId", UserSubmission.ShowSubmissionByEventIDView, name="showsubmissionbyeventid"),

#=================================================CRITERIA================================================

    path("CreateCriteria", EventCriteria.CreateCriteriaView, name="createcriteria"),
    path("ShowCriteria", EventCriteria.ShowCriteriaByEventIdView, name="showcriteria"),

#=================================================REVIEW======================================================

    path("CreateReview", SubmissionReview.CreateReviewView, name="createreview"),
    path("ShowReview", SubmissionReview.ShowReviewBySubmissionIdView, name="showreview"),

#==================================================ORGANIZER==================================================

    path("AppOrRej", OrganizerCheck.AppOrRejView, name="approveorreject"),
    path("CreateRanking", OrganizerCheck.CreatePositionView, name="createranking"),
    path("ShowRanking", OrganizerCheck.ShowEventRankingsView, name="showranking"),

#===================================================CERTIFICATE============================================

    path("CreateCertificate", OrganizerCheck.CreateCertificateView, name="createcertificate"),

#===============================================aefsrzhtgs============================================

    path("AssignSpeaker", OrganizerCheck.AssignSpeakerView, name="createspeaker"),
    path("GetSpeakerList", OrganizerCheck.GetSpeakerView, name="getspeakerlist"),

#====================================================   ABSTRACT SUBMISSION    ===================================

    path("CreateAbstract", SubmitAbstract.CreateAbstractView, name="createabstract"),
    path("GetAllAbstract", SubmitAbstract.GetAllAbstractView, name="getallabstract"),
    path("GetAbstractByUserId", SubmitAbstract.GetAbstractByUserIdView, name="getabstractbyuserid"),
    path("GetAbstractById", SubmitAbstract.GetAbstractByIdView, name="getabstractbyid"),
    path("GetAbstractByEventId", SubmitAbstract.GetAbstractByEventIdView, name="getabstractbyeventid"),
    path("UpdateAbstract", SubmitAbstract.UpdateAbstractView, name="updateabstract"),

    path("ReviewAbstract", ReviewAbstract.as_view(), name="reviewabstract"),
    path("GetAbstractReview", ReviewAbstract.GetAbstractReview, name="getabstractreview"),

#==========================================TIMESLOT==============================================

    path("CreateTimeslot", ConferenceTimeslot.CreateTimeslot, name="createtimeslot"),
    path("GetAllTimeslots", ConferenceTimeslot.as_view(), name="getalltimeslots"),
    path("GetTimeslotByEventId", ConferenceTimeslot.ShowTimeslotByEventId, name="gettimeslotbyeventid"),
    path("UpdateTimeslot", ConferenceTimeslot.UpdateTimeslotView, name="updatetimeslot"),
    path("AddTimeslot", ConferenceTimeslot.AddTimeslotView, name="updatetimeslot"),
    path("DeleteTimeslot", ConferenceTimeslot.DeleteTimeslotView, name="deletetimeslotview"),

    path("SelectTimeslot", ConferenceTimeslot.SelectTimeslotView, name="selecttimeslot"),
    path("GetSelectedSlotById", ConferenceTimeslot.GetSelectedSlotById, name="getselectedslotbyid"),
    path("GetSelectedSlotBySubmissionId", ConferenceTimeslot.GetSelectedSlotBySubmissionId, name="getselectedslotbysubmissionid"),


    path("GetPresentationConfirmationData", ConferenceTimeslot.GetPresentationConfirmationDataView, name="GetPresentationConfirmationData"),

#===================================================RESULT_DECLARATION=========================================

    path("CreateResultDeclaration", ResultDeclaration.CreateResultDeclarationView, name="createresultdeclaration"),


]
