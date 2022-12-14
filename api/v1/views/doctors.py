#!/usr/bin/python3
"""
a new view for Doctor objects that handles
all default RESTFul API actions:
"""
from flask import jsonify, abort, make_response, request
from models import database_storage
from models.doctor import Doctor
from models.patient import Patient
from models.office_hours import OfficeHours
from models.distance import Distance
from models.office import Office
from api.v1.views import app_views
from sqlalchemy import update
from models.doctor import doctor_specialization
from models.specialization import Specialization
# from flasgger.utils import swag_from
import requests
import random
import json
import os


@app_views.route('/doctors',
                 methods=['GET'],
                 strict_slashes=False)
# @swag_from('documentation/doctor/get_doctor.yml',
#           methods=['GET'])
def get_doctors():
    """
    Retrieves the list of all Doctor objects
    note; to_dict method is customised(class name, id,
    created & updated at)
    """
    all_doctors = database_storage.all(Doctor).values()
    list_doctors = []
    for doctor in all_doctors:
        list_doctors.append(doctor.to_dict())
    return jsonify(list_doctors)


@app_views.route('/doctors/<doctor_id>',
                 methods=['GET'],
                 strict_slashes=False)
# @swag_from('documentation/doctor/get_id_doctor.yml',
#           methods=['get'])
def get_doctor(doctor_id):
    """ Retrieves a specific Doctor object """
    doctor = database_storage.get_byID(Doctor, doctor_id)
    if not doctor:
        abort(404)

    return jsonify(doctor.to_dict())


@app_views.route('/doctors/<doctor_id>',
                 methods=['DELETE'],
                 strict_slashes=False)
# @swag_from('documentation/doctor/delete_doctor.yml',
#           methods=['DELETE'])
def delete_doctor(doctor_id):
    """Deletes a Doctor Object"""

    doctor = storage.get_byID(Doctor, doctor_id)

    if not doctor:
        abort(404)

    database_storage.delete(doctor)
    database_storage.save()

    return make_response(jsonify({}), 200)


@app_views.route('/doctors',
                 methods=['POST'],
                 strict_slashes=False)
# @swag_from('documentation/doctor/post_doctor.yml',
#           methods=['POST'])
def post_doctor():
    """Creates a Doctor"""
    if not request.get_json():
        abort(400, description="Not a JSON")

    details = ["user_name", "email", "password",
               "first_name", "last_name", "gender",
               "phone_number", "birthdate"]
    for detail in details:
        if detail not in request.get_json():
            abort(400, description="Missing" + detail)

    data = request.get_json()
    doctor = Doctor(**data)
    doctor.save()
    return make_response(jsonify(doctor.to_dict()), 201)


@app_views.route('/doctors/<doctor_id>',
                 methods=['PUT'],
                 strict_slashes=False)
# @swag_from('documentation/doctor/put_doctor.yml',
#           methods=['PUT'])
def put_doctor(doctor_id):
    """Updates a Doctor"""
    doctor = database_storage.get_byID(Doctor, doctor_id)
    if not doctor:
        abort(404)

    if not request.get_json():
        abort(400, description="Not a JSON")

    ignore = ['id', 'created_at', 'updated_at']

    data = request.get_json()
    for key, value in data.items():
        if key not in ignore:
            setattr(doctor, key, value)
    database_storage.save()
    return make_response(jsonify(doctor.to_dict()), 200)

@app_views.route('/doctors_search/<patient_id>',
                 methods=['POST'],
                 strict_slashes=False)
# @swag_from('documentation/doctor/post_doctor.yml',
#           methods=['POST'])
def doctors_search(patient_id):
    """Retrieve info for booking"""
    if request.get_json():
        params = request.get_json()
        latitude1 = params.get('latitude')
        longitude1 = params.get('longitude')
        # 1- update patient geocodes
        database_storage.session.query(Patient).filter(
            Patient.id == patient_id).update(
                {Patient.latitude: latitude1,
                 Patient.longitude: longitude1})
        database_storage.save()
        
        #patient = database_storage.get_byID(Patient, patient_id)

        # 2- get offices and update distances
        offices = database_storage.all(Office).values()
        gma_check = 0

        # update the distance between the office and the patient
        for office in offices:
            url1 = "https://maps.googleapis.com/maps/api/distancematrix/json?origins="
            origin_lat = str(latitude1)
            origin_long = str(longitude1)
            dest_lat = str(office.latitude)
            dest_long = str(office.longitude)
            API_KEY = os.environ.get('ARC_GOOGLE_API_KEY')
            url2 = url1 + origin_lat + "%2C" + origin_long
            url3 = url2 + "&destinations=" + dest_lat + "%2C" + dest_long
            url = url3 + "&key=" + API_KEY
            payload={}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            data = response.json()
            if data['rows'][0]['elements'][0]['status'] == "OK":
                gma_check += 1
                database_storage.session.query(
                    Distance).filter(
                        Distance.patient_id == patient_id
                        ).filter(
                            Distance.office_id == office.id
                            ).update({
                                Distance.distance_text: data['rows'][0]['elements'][0]['distance']['text'],
                                Distance.distance: data['rows'][0]['elements'][0]['distance']['value']
                                })
                database_storage.save()
        # 3 - call for data with distances
        if gma_check:        
            objs = database_storage.session.query(Doctor,
                                                  Specialization,
                                                  Office,
                                                  Distance,
                                                  OfficeHours
                                                  ).filter(
                                                    Doctor.id == Office.doctor_id
                                                  ).filter(
                                                    Office.id == Distance.office_id
                                                  ).filter(
                                                    Distance.patient_id == patient_id
                                                  ).filter(
                                                    Office.id == OfficeHours.office_id
                                                  ).filter(
                                                    OfficeHours.availability == "Yes"
                                                  ).filter(
                                                    Specialization.id == doctor_specialization.c.specialization_id
                                                  ).filter(
                                                    doctor_specialization.c.doctor_id == Doctor.id
                                                  ).all()
            dico = [{'doctor': obj[0].to_dict(),
                    'specialization': obj[1].to_dict(),
                    'office': obj[2].to_dict(),
                    'distance': obj[3].to_dict(),
                    'office_hour': obj[4].to_dict()} for obj in objs]
            return (jsonify(dico))

        if gma_check == 0:
            objs = database_storage.session.query(Doctor,
                                                  Specialization,
                                                  Office,
                                                  OfficeHours
                                                  ).filter(
                                                    Doctor.id == Office.doctor_id
                                                  ).filter(
                                                    Office.id == OfficeHours.office_id
                                                  ).filter(
                                                    OfficeHours.availability == "Yes"
                                                  ).filter(
                                                    Specialization.id == doctor_specialization.c.specialization_id
                                                  ).filter(
                                                    doctor_specialization.c.doctor_id == Doctor.id
                                                  ).all() 
            dico = [{'doctor': obj[0].to_dict(),
                     'specialization': obj[1].to_dict(),
                     'office': obj[2].to_dict(),
                     'office_hour': obj[3].to_dict()} for obj in objs]
            return (jsonify(dico))

    # when there is no address given in the request
    else:
        objs = database_storage.session.query(Doctor,
                                              Specialization,
                                              Office,
                                              OfficeHours
                                              ).filter(
                                                Doctor.id == Office.doctor_id
                                              ).filter(
                                                Office.id == OfficeHours.office_id
                                              ).filter(
                                                OfficeHours.availability == "Yes"
                                              ).filter(
                                                Specialization.id == doctor_specialization.c.specialization_id
                                              ).filter(
                                                doctor_specialization.c.doctor_id == Doctor.id
                                              ).all() 
        dico = [{'doctor': obj[0].to_dict(),
                 'specialization': obj[1].to_dict(),
                 'office': obj[2].to_dict(),
                 'office_hour': obj[3].to_dict()} for obj in objs]
        return (jsonify(dico))
