import os
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from flask import Flask, flash, request, redirect, url_for, send_from_directory,send_file
from werkzeug.utils import secure_filename
import datetime
import pandas as pd
import csv
from re import sub
import numpy as np
import re

observaciones = Blueprint('observaciones', __name__)


UPLOAD_FOLDER = '/tmp'
OBSERVACIONES_DOWNLOAD = "app/observaciones/download"
ALLOWED_EXTENSIONS = {'ods', 'xls', 'xlsx'}
def procesar(filename):
    df = pd.read_excel(UPLOAD_FOLDER + "/" +filename, sheet_name = 'Datos', converters={'Programa':str})
    df = df.sort_values(by=['Ejercicio', 'Motivo'])
    df['Nombre Cr.Delegado'] = df['Nombre Intervención']
    df['Nombre Cr.Delegado reiteración'] = df['Nombre intervención por reiteración']
    df['Fecha Observación'] = pd.to_datetime(df['Fecha Intervención']).dt.date
    df['Prog'] = df['Programa'].astype(int)
    df['Prog'] = df['Prog'] //100
    df['Prog'] = df['Prog'] %1000


    df = df[['Ejercicio','Excedido' , 'Documento','Rubro','Programa','Nombre Programa','Nombre Acreedor','Importe en MN' , 'Fecha Ordenador','Nombre Ordenador' ,  \
          'Fecha Observación',	'Nombre Cr.Delegado','Motivo' ,'Fecha Reiteracíon','Nombre Reiteración','Comentario reiteración' , 	'Fecha intervención por reiteración' ,	\
          'Nombre Cr.Delegado','Prog']]

    SYJ = df[df.Documento.str.contains('SYJ')].drop(columns='Prog')
    df = df[~df.Documento.str.contains('SYJ')]


    SanCarlos = df[df.Prog == 101].drop(columns='Prog')
    Aigua = df[df.Prog == 154].drop(columns='Prog')
    Maldonado = df[df.Prog == 160].drop(columns='Prog')
    Garzon = df[df.Prog == 156].drop(columns='Prog')
    PanDeAzucar = df[df.Prog == 153].drop(columns='Prog')
    Piriapolis =  df[df.Prog == 157].drop(columns='Prog')
    PdelEste = df[df.Prog == 155].drop(columns='Prog')
    Solis = df[df.Prog == 158].drop(columns='Prog')


    Intendencia = df[~df.Prog.isin([101,154,160,156,153,157,155,158])].drop(columns='Prog')

    writer = pd.ExcelWriter(os.path.join(observaciones.root_path, "download/") + "InformeObservaciones.xlsx", date_format = 'DD/MM/YYYY', datetime_format='DD/MM/YYYY')
    Intendencia.to_excel(writer, sheet_name="Intendencia", index=False)
    SYJ.to_excel(writer, sheet_name="SYJ", index=False)
    Aigua.to_excel(writer, sheet_name="Aigua", index=False)
    Garzon.to_excel(writer, sheet_name="Garzon", index=False)
    Maldonado.to_excel(writer, sheet_name="Maldonado", index=False)
    PanDeAzucar.to_excel(writer, sheet_name="PanDeAzucar", index=False)
    Piriapolis.to_excel(writer, sheet_name="Piriapolis", index=False)
    PdelEste.to_excel(writer, sheet_name="PdelEste", index=False)
    SanCarlos.to_excel(writer, sheet_name="SanCarlos", index=False)
    Solis.to_excel(writer, sheet_name="Solis", index=False)

    writer.close()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@observaciones.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No seleccionó archivo', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            file.save(os.path.join(UPLOAD_FOLDER, filename))

            salida = procesar(filename)


            return render_template('observaciones/resultado.html', salida = salida)
        else:
            flash('Archivo no válido',  'error')
            return redirect(request.url)
    else:
        return render_template('observaciones/index.html', now=datetime.datetime.now())
    return ''

@observaciones.route('/down/pepe', methods=['GET', 'POST'])
def pepe():
    print('lala')
    return "fdfsf"

@observaciones.route('/download/<path:filename>', methods=['GET', 'POST'])
def download_file(filename):
    return send_from_directory(directory=os.path.join(observaciones.root_path, "download/"), filename=filename)
