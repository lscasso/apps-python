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

atyro = Blueprint('atyro', __name__)

"""
@atyro.route('/')
@login_required
def index():
    print('Hello world!', file=sys.stderr)
    atyro.logger.error('testing info log')
    return render_template('atyro/index.html')

"""


UPLOAD_FOLDER = '/home/lscasso/tmp'
ATYRO_DOWNLOAD = "app/atyro/download"
ALLOWED_EXTENSIONS = {'ods', 'xls', 'xlsx'}
def procesar(filename,nMes ,nAno):

    if  int(nMes) < 10:
        mes = "0" +nMes  + nAno
    else:
        mes = nMes + nAno
    linea1 = [1,'N',3.1,'Atyro Intendencia','0000007632174','00100055980011',1,'INTENDENCIA DE MALDONADO','FRANCISCO ACUÑA DE FIGUEROA Y BURNET','4221921']
    f=open( os.path.join(atyro.root_path, "download/") +  "nomina.bps",'w', encoding='ISO-8859-1')
    writer = csv.writer(f, delimiter='|',quoting=csv.QUOTE_NONE, quotechar='',escapechar='\\')

    dfBPS = pd.read_excel(UPLOAD_FOLDER + "/" + filename,sheet_name="BPS")
    dfPagos = pd.read_excel(UPLOAD_FOLDER + "/" + filename,sheet_name="Hoja1",header=0)
    dfJoin = dfBPS.merge(dfPagos,left_on='DOCUMENTO',right_on='CEDULA',how='right',indicator=True)
    right = dfJoin[dfJoin['_merge'] == 'right_only']

    dfJoin = dfJoin[dfJoin['_merge'] != 'right_only']

    dfJoin['PAIS'] = dfJoin['PAIS'].fillna(int(1))
    dfJoin['TIPO'] = dfJoin['TIPO'].fillna('DO')
    dfJoin['REMUNERACION'] =  dfJoin['REMUNERACION BPS']
    dfJoin['FECHA_NAC'] =  dfJoin['F_NACIMIENTO'].apply(lambda x: x.strftime("%d%m%Y"))
    #dfJoin['FECHA_NAC'] = dfJoin['F_NACIMIENTO']
    dfJoin['FECHA_ING'] =  dfJoin['FECHA_INGRESO'].apply(lambda x: x.strftime("%d%m%Y"))
    #dfJoin['FECHA_ING'] = dfJoin['FECHA_INGRESO']
    dfJoin['Enfermedad'] = 4
    dfJoin["D"] =  pd.to_datetime(dfJoin["D"], format="%d/%m/%y")
    dfJoin['D'] =  dfJoin['D'].apply(lambda x:  x.strftime("%d%m%Y") if not pd.isnull(x)  or x > 0  else "")
    dfJoin['D'] =  dfJoin['D'].apply(lambda x: "" if x == "30121899" else x)
    dfJoin['D'] =  dfJoin['D'].apply(lambda x: "" if x == "30121999" else x)
    dfJoin["D"].fillna("", inplace = True)
    dfJoin["CB"].fillna(0, inplace = True)

    dfJoin['NACIONALIDAD'] = dfJoin['NACIONALIDAD'].fillna(int(1))
    dfJoin['NACIONALIDAD'] = dfJoin['NACIONALIDAD'].astype(int)
    dfJoin['DOCUMENTO'] = dfJoin['DOCUMENTO'].astype(int)
    dfJoin['PAIS'] = dfJoin['PAIS'].astype(int)
    total = dfJoin['REMUNERACION'].sum()
    writer.writerow(linea1)
    writer.writerow([4,mes,87, "{:.2f}".format(total),'',''])
    for index, row in dfJoin.iterrows():
        writer.writerow([5,row['PAIS'],row['TIPO'],row['DOCUMENTO'],row['APELLIDO_1'],row['APELLIDO_2'],row['NOMBRE_1'],row['NOMBRE_2'],row['FECHA_NAC'],int(row['SEXO']),row['NACIONALIDAD']])
        writer.writerow([6,'',row['PAIS'],row['TIPO'],row['DOCUMENTO'],1,row['FECHA_ING'],2,99,133,9,99,'','','N',row['DT NOMINA'],0,  \
                     12 if row['Enfermedad'] <= 6 else 6, "" if row['CB'] == 0 else row['CB'],row['D']])
        writer.writerow([7,'',row['PAIS'],row['TIPO'],row['DOCUMENTO'],1,1,"{:.2f}".format(row['REMUNERACION']),"",""])
    f.close()
    return right['CEDULA']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@atyro.route('/', methods=['GET', 'POST'])
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
            mes = request.form.get('mes')
            ano = request.form.get('ano')
            print(mes)
            salida = procesar(filename,mes,ano)


            return render_template('atyro/resultado.html', salida = salida)
        else:
            flash('Archivo no válido',  'error')
            return redirect(request.url)
    else:
        return render_template('atyro/index.html', now=datetime.datetime.now())
    return ''

@atyro.route('/down/pepe', methods=['GET', 'POST'])
def pepe():
    print('lala')
    return "fdfsf"

@atyro.route('/download/<path:filename>', methods=['GET', 'POST'])
def download_file(filename):
    return send_from_directory(directory=os.path.join(atyro.root_path, "download/"), filename=filename)
