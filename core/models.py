from django.db import models
from django.db.models import Model

#================================================LOGS========================================================

class Logs(Model):
    logfield = models.CharField(max_length=255)
    logtype = models.CharField(max_length=255)
    prelogdetails = models.JSONField()
    postlogdetails = models.JSONField()
    log_user_id = models.CharField(max_length=255)
    logip = models.CharField(max_length=50)
    created_on = models.DateTimeField(max_length=6, auto_now=True)

    class Meta:
        managed = False
        db_table = "EVENT_LOG"

#================================================USER========================================================

class AuthGroup(Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'

class AuthUser(Model):
    password = models.CharField(max_length=128)
    k_id = models.CharField(max_length=255)
    last_login = models.DateTimeField(blank=True, null=True)
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(unique=True ,max_length=254)
    mobileno = models.CharField(unique=True, max_length=255)
    is_active = models.IntegerField(default=1)
    unique_id = models.CharField(max_length=255)
    date_joined = models.DateTimeField(auto_now=True)       

    class Meta:
        managed = False
        db_table = 'auth_user'

class AuthUserGroups(Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


#================================================TRACK========================================================

class Track(Model):
    track_id = models.CharField(max_length=20)
    track_name = models.CharField(max_length=255)
    # topic = models.TextField()
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'EVENT_TRACK'

#================================================EVENT========================================================

class Event(Model):
    event_id = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    shortform = models.CharField(max_length=255, unique=True)
    orga_email = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    reg_link = models.CharField(max_length=255)
    event_color = models.CharField(max_length=7, null = True, blank = True)
    logo = models.CharField(max_length=255)
    header_image = models.CharField(max_length=255, null = True, blank = True)
    landing_text = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=0)
    track_id = models.CharField(max_length=255)
    created_by = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="created_by")
    created_on = models.DateTimeField()
    updated_on = models.DateTimeField(auto_now=True)
    criteria = models.JSONField()
    position = models.CharField(max_length = 500)
    speaker = models.CharField(max_length=500)
    abs_start = models.DateField()
    abs_end = models.DateField()

    class Meta:
        managed = False
        db_table = 'EVENT'

#=================================================REVIEWER===================================================

class Reviewer(Model):
    event_id = models.ForeignKey(Event, models.DO_NOTHING, db_column="event_id")
    user_id = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="user_id")

    class Meta:
        managed="False"
        db_table = 'REVIEWER'

#====================================================TOPIC=========================================================

class Topic(Model):
    trackid = models.ForeignKey(Track, models.DO_NOTHING, db_column="trackid")
    topic = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'EVENT_TRACK_TOPIC'

#================================================SUBMISSION========================================================

class Submission(Model):
    user_id=models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="user_id", null=True, blank=True)
    title = models.CharField(max_length=50)
    description = models.TextField()
    paperupload = models.CharField(max_length=255)
    submission_id = models.CharField(max_length=20)
    created_on = models.DateTimeField()
    updated_on = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length = 255)
    event_id = models.ForeignKey(Event, models.DO_NOTHING, db_column = "event_id")
    track_id = models.ForeignKey(Track, models.DO_NOTHING, db_column= "track_id")
    topic_id = models.ForeignKey(Topic, models.DO_NOTHING, db_column="topic_id")
    participants = models.JSONField()
    team_composition = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'CORE_SUBMISSION'

#================================================ABSTRACT========================================================

class Abstract(Model):
    user_id=models.ForeignKey(AuthUser, models.DO_NOTHING, db_column="user_id", null=True, blank=True)
    abstract = models.CharField(max_length=255)
    created_on = models.DateTimeField()
    updated_on = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length = 100)
    event_id = models.ForeignKey(Event, models.DO_NOTHING, db_column = "event_id")
    track_id = models.ForeignKey(Track, models.DO_NOTHING, db_column= "track_id")
    topic_id = models.ForeignKey(Topic, models.DO_NOTHING, db_column="topic_id")
    reviewed_by = models.ForeignKey(Reviewer, models.DO_NOTHING, db_column = "reviewed_by")
    remarks = models.CharField(max_length=500)

    class Meta:
        managed = False
        db_table = 'ABSTRACT'

#=======================================================CERTIFICATE==========================================

class Certificate(Model):
    certificate_id = models.CharField(max_length=255)
    certificate = models.CharField(max_length=255)
    submission_id = models.ForeignKey(Submission, models.DO_NOTHING, db_column = "submission_id")

    class Meta:
        managed = False
        db_table = 'CERTIFICATE'

#==========================================================REVIEW_MARKS================================================

class ReviewSubmission(Model):
    submission_id = models.ForeignKey(Submission, models.DO_NOTHING, db_column = "submission_id")
    criteria = models.CharField(max_length=500, db_column="criteria", null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    feedback = models.CharField(max_length=500)
    total_marks = models.IntegerField()
    reviewed_by = models.ForeignKey(Reviewer, models.DO_NOTHING, db_column = "reviewed_by")

    class Meta:
        managed = False
        db_table = 'SUBMISSION_REVIEW'

#==========================================================TIMESLOT================================================

class TimeSlot(Model):
    event_id = models.ForeignKey(Event, models.DO_NOTHING, db_column= "event_id")
    # created_by = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column = "created_by")
    # date = models.DateField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    mode = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = "TIMESLOTS"

#===================================================CONFERENCE_PRESENTATION===========================================

class ConferencePresentation(Model):
    submission_id = models.ForeignKey(Submission, models.DO_NOTHING, db_column = "submission_id")
    timeslot_id = models.ForeignKey(TimeSlot, models.DO_NOTHING, db_column = "timeslot_id")
    confirmed_participants = models.JSONField()
    status = models.CharField(max_length=45, default="participant")
    position = models.IntegerField(null = True, blank=True)
    prize = models.IntegerField()
    created_on = models.DateTimeField()
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        managed= False
        db_table = "CONFERENCE_PRESENTATION"


