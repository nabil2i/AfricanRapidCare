#!/usr/bin/python3
"""
a new view for Patient objects that handles
all default RESTFul API actions:
"""
from flask import jsonify, abort, make_response, request
from models import database_storage
from models.patient import Patient
from api.v1.views import app_views
from models.appointment import Appointment
from models.doctor import Doctor
from models.office import Office
from models.appointment_status import AppointmentStatus
from models.distance import Distance
from sqlalchemy import update
from models.doctor import doctor_specialization
from models.specialization import Specialization
# from flasgger.utils import swag_from


@app_views.route('/patients',
                 methods=['GET'],
                 strict_slashes=False)
# @swag_from('documentation/patient/get_patient.yml',
#           methods=['GET'])
def get_patients():
    """
    Retrieves the list of all Patient objects
    note; to_dict method is customised(class name, id,
    created & updated at)
    """
    all_patients = database_storage.all(Patient).values()
    list_patients = []
    for patient in all_patients:
        list_patients.append(patient.to_dict())
    return jsonify(list_patients)


@app_views.route('/patients/<patient_id>',
                 methods=['GET'],
                 strict_slashes=False)
# @swag_from('documentation/patient/get_id_patient.yml',
#           methods=['get'])
def get_patient(patient_id):
    """ Retrieves a specific Patient object """
    patient = database_storage.get_byID(Patient, patient_id)
    if not patient:
        abort(404)

    return jsonify(patient.to_dict())


@app_views.route('/patients/<patient_id>',
                 methods=['DELETE'],
                 strict_slashes=False)
# @swag_from('documentation/patient/delete_patient.yml',
#           methods=['DELETE'])
def delete_patient(patient_id):
    """Deletes a Patient Object"""

    patient = storage.get_byID(Patient, patient_id)

    if not patient:
        abort(404)

    database_storage.delete(patient)
    database_storage.save()

    return make_response(jsonify({}), 200)


@app_views.route('/patients',
                 methods=['POST'],
                 strict_slashes=False)
# @swag_from('documentation/patient/post_patient.yml',
#           methods=['POST'])
def post_patient():
    """Creates a Patient"""
    if not request.get_json():
        abort(400, description="Not a JSON")

    details = ["user_name", "email", "password",
               "first_name", "last_name", "gender",
               "phone_number", "birthdate"]
    for detail in details:
        if detail not in request.get_json():
            abort(400, description="Missing" + detail)

    data = request.get_json()
    patient = Patient(**data)
    patient.save()
    return make_response(jsonify(patient.to_dict()), 201)


@app_views.route('/patients/<patient_id>',
                 methods=['PUT'],
                 strict_slashes=False)
# @swag_from('documentation/patient/put_patient.yml',
#           methods=['PUT'])
def put_patient(patient_id):
    """Updates a Patient"""
    patient = database_storage.get_byID(Patient, patient_id)

    if not patient:
        abort(404)

    if not request.get_json():
        abort(400, description="Not a JSON")

    ignore = ['id', 'created_at', 'updated_at']

    data = request.get_json()
    for key, value in data.items():
        if key not in ignore:
            setattr(patient, key, value)
    database_storage.save()
    return make_response(jsonify(patient.to_dict()), 200)

@app_views.route('/patients/<string:patient_id>/appointments',
                 methods=['POST'],
                 strict_slashes=False)
# @swag_from('documentation/appointment/put_appointment.yml',
#           methods=['PUT'])
def get_patient_appointment(patient_id):
    """Updates a appointment"""
    patient = database_storage.get_byID(Patient, patient_id)

    if not patient:
        abort(404)

    objs = database_storage.session.query(Appointment,
                                          Office,
                                          Distance,
                                          Doctor,
                                          Specialization,
                                          AppointmentStatus
                                          ).filter(
                                              Appointment.patient_id == patient_id   
                                          ).filter(
                                           Appointment.office_id == Office.id   
                                          ).filter(
                                            Appointment.appointment_status_id == AppointmentStatus.id  
                                          ).filter(
                                              Office.doctor_id == Doctor.id
                                          ).filter(
                                            Office.id == Distance.office_id
                                          ).filter(
                                            Distance.patient_id == patient_id
                                          ).filter(
                                            Specialization.id == doctor_specialization.c.specialization_id
                                          ).filter(
                                            doctor_specialization.c.doctor_id == Doctor.id
                                          ).all()

    dico = [{'appointment': obj[0].to_dict(),
             'office': obj[1].to_dict(),
             'distance': obj[2].to_dict(),
             'doctor': obj[3].to_dict(),
             'specialization': obj[4].to_dict(),
             'status': obj[5].to_dict()} for obj in objs]
    return (jsonify(dico))
