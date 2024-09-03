import os
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
from django.conf import settings
import environ
from virtual_conference.settings import AUTHFKEY
from django.conf import settings
from datetime import datetime
from core.models import *
from core.serializer import *
from django.core.exceptions import ObjectDoesNotExist
from datetime import date,datetime
from django.core.files.temp import NamedTemporaryFile
from django.core.files.storage import default_storage
from PIL import Image, ImageFont, ImageDraw
import qrcode

cipher = Cipher(algorithms.AES(AUTHFKEY), modes.ECB(), backend=default_backend())


def data_encrypt(**data):
    l = {}
    for keys in data:
         if type(data[keys]) != str:
              data[keys]=str(data[keys])
         
         encryptor = cipher.encryptor()
         padder = padding.PKCS7(algorithms.AES.block_size*4).padder()
         padded_plaintext = padder.update(data[keys].encode()) + padder.finalize()
         ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
         text = base64.b64encode(ciphertext)
         l.update({keys:text.decode()})
    return l


def data_decrypt(**data):
    l = {}
    for keys in data:
        try :
           decryptor = cipher.decryptor()
           
           decrypted_padded_plaintext = decryptor.update(base64.b64decode(data[keys].encode())) + decryptor.finalize()
           
           # Removing padding
           unpadder = padding.PKCS7(algorithms.AES.block_size*4).unpadder()
           decrypted_plaintext = unpadder.update(decrypted_padded_plaintext) + unpadder.finalize()
           text = decrypted_plaintext
           l.update({keys:text.decode()})
        except ValueError:
             pass
    return l


def uploadLogo(file, request, uploadDir, shortform):
     uploadDir = os.path.join(uploadDir)
     if not os.path.exists(os.path.join(str(settings.BASE_DIR ) +  uploadDir)):
          os.makedirs(os.path.join(str(settings.BASE_DIR) + uploadDir))
     Name, Extension = os.path.splitext(file.name)
     fileName =  "logoimg" + shortform + Extension
     logopath = os.path.join(str(settings.BASE_DIR)) + uploadDir + fileName
     with open(logopath, 'wb+') as destination:
          for chunk in file.chunks():
               destination.write(chunk)
     return fileName

def uploadHeaderImage(file, request, uploadDir, shortform):
     uploadDir = os.path.join(uploadDir)
     if not os.path.exists(os.path.join(str(settings.BASE_DIR ) +  uploadDir)):
          os.makedirs(os.path.join(str(settings.BASE_DIR) + uploadDir))
     Name, Extension = os.path.splitext(file.name)
     fileName =  "headerimg" + shortform + Extension
     logopath = os.path.join(str(settings.BASE_DIR)) + uploadDir + fileName
     with open(logopath, 'wb+') as destination:
          for chunk in file.chunks():
               destination.write(chunk)
     return fileName

def CreateEventId(eventID):
     event = Event.objects.get(id=eventID)
     eventData = {"event_id": "ISEAEV" + str(eventID)}
     ser = EventIDSerializer(event, data= eventData)
     ser.is_valid(raise_exception=True)
     ser.save()

def CreateTrackId(trackID):
     track = Track.objects.get(id = trackID)
     trackData = {"track_id": "ISEATR" + str(trackID)}
     ser = TrackIDSerializer(track, data= trackData)
     ser.is_valid(raise_exception=True)
     ser.save()

def validate_submission(paper):
    if type(paper) == str:
        if paper != "null":
            return False
    else:
        file_type = magic.from_buffer(paper.read(1024), mime = True)
        valid_filetype = ['application/pdf', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/zip']
        if file_type not in valid_filetype:
            raise serializers.ValidationError({
                "errors": "Invalid Filetype, '.pdf' and '.pptx' are allowed"
            })
        
        filesize = paper.size
        megabyte_limit = 4
        valid_extensions = ['.pdf', '.pptx']

        ext = os.path.splitext(paper.name)[1].lower()

        if ext not in valid_extensions:
            raise serializers.ValidationError({
                "errors": "Invalid Filetype, '.pdf' and '.pptx' are allowed"
            })
           
        
        if filesize > megabyte_limit *1024 * 1024:
            raise serializers.ValidationError({
                "errors": "File size should not exceed 2MB"
            })
        
        if '.' in ext[:-5]:
            raise serializers.ValidationError({
                "errors": "Invalid Filetype, double extensions are not allowed"
            })
        
        else:
            return True

def uploadPaper(file, request, uploadDir, userid, trackid, topicid):
    uploadDir = os.path.join(uploadDir)
    if not os.path.exists(os.path.join(str(settings.BASE_DIR) + uploadDir + str(userid))):
        os.makedirs(os.path.join(str(settings.BASE_DIR) + uploadDir + str(userid)))
    extension = os.path.splitext(file.name)[1]
    filename = "UserSubmissionIVP" + str(trackid) + str(topicid) + str(userid) + extension

    submissionpath = os.path.join(str(settings.BASE_DIR)) + uploadDir + str(userid) + "/" + filename 
    
    with open(submissionpath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return filename

def uploadAbstract(file, request, uploadDir, userid, trackid, topicid):
    uploadDir = os.path.join(uploadDir)
    if not os.path.exists(os.path.join(str(settings.BASE_DIR) + uploadDir + str(userid))):
        os.makedirs(os.path.join(str(settings.BASE_DIR) + uploadDir + str(userid)))
    extension = os.path.splitext(file.name)[1]
    filename = "UserAbstractIVP" + str(trackid) + str(topicid) + str(userid) + extension

    submissionpath = os.path.join(str(settings.BASE_DIR)) + uploadDir + str(userid) + "/" + filename 
    
    with open(submissionpath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return filename

def CreateSubmissionId(subID,topicId,trackId):
    sub = Submission.objects.get(id = subID)
    subData = {"submission_id": f"ISEASUB{subID}TR{trackId}TO{topicId}" }
    ser = SubmissionIDSerializer(sub, data = subData)
    ser.is_valid(raise_exception=True)
    ser.save()
     
def isDateinRange(start_date, end_date, today):
    # print("startDate",start_date)
    # print("EndDAte",end_date)
    
    # print("Today", today)
    # print("start", isinstance(start_date,date))
    # print("end", isinstance(end_date,date))
    # print("current", isinstance(today,date))
    #if today >= start_date and today <= end_date:
    if start_date <= today <= end_date:
        return True
    else:
        return False
    
def validate_rating(rating):
    if isinstance(rating, int) and (1 <= rating <= 5):
        return True
    
# Global Variables
fontpath = os.path.join(settings.BASE_DIR ,"static", "Font", "GreatVibes-Regular.ttf")
FONT_FILE = ImageFont.truetype(fontpath, 80)
FONT_COLOR = "#000000"

templatepath = os.path.join(settings.BASE_DIR, "static", "ISEAsample.jpeg")
template = Image.open(templatepath)
WIDTH, HEIGHT = template.size

def make_certificates(name,topic,event,track, uploadDir):
    '''Function to save certificates as a .jpeg file'''
    image_source = template.copy()
    draw = ImageDraw.Draw(image_source)

    # Finding the width and height of the text using textbbox
    bbox = draw.textbbox((0, 0), name, font=FONT_FILE)
    name_width = bbox[2] - bbox[0]
    name_height = bbox[3] - bbox[1]

    
    draw.text(((WIDTH - name_width) / 2 +210, HEIGHT * 0.30 +40), name, fill=FONT_COLOR, font=FONT_FILE)

    topic = topic.lower()
    draw2 = ImageDraw.Draw(image_source)
    bbox2 = draw2.textbbox((0, 0), topic, font=FONT_FILE)
    topic_width = bbox2[2] - bbox2[0] 
    topic_height = bbox2[3] - bbox2[1] 
 
    draw2.text(((WIDTH - topic_width) / 2 , (HEIGHT - topic_height)/2 - 40), topic, fill=FONT_COLOR, font=FONT_FILE)

    #qrcode
    qr = qrcode.QRCode(
        version=12,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=2,
        border=4
    )
    # qr.add_data(f"Name : {name}, Topic : {topic}")
    data = {'name': name ,'conference' : event, 'track' : track, 'topic' : topic}
    qr.add_data(data)
    qr.make()
    qr_img = qr.make_image()
    qr_img = qr_img.convert("RGBA")
    qr_width, qr_height = qr_img.size
    position = (50, HEIGHT - qr_height - 60)
    image_source.paste(qr_img, position, qr_img)

    uploadDir = os.path.join(uploadDir)
    if not os.path.exists(os.path.join(str(settings.BASE_DIR) + uploadDir )):
        os.makedirs(os.path.join(str(settings.BASE_DIR) + uploadDir ))

    filename = name+ datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpeg"
    filepath = os.path.join(str(settings.BASE_DIR)) + uploadDir + filename

    # Saving the certificates in a different directory.
    image_source.save(os.path.join(filepath))

    return filename


def CreateCertificateId(certID, eventID):
     cert = Certificate.objects.get(id = certID)
     certData = {"certificate_id": f"ISEA/IC/CF{eventID}/{certID}"}
     ser = CreateCertificateIDSerializer(cert, data = certData)
     ser.is_valid(raise_exception=True)
     ser.save()






        
    