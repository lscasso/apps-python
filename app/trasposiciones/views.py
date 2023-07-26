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
import shutil

trasposiciones = Blueprint('trasposiciones', __name__)


UPLOAD_FOLDER = '/tmp'
ATYRO_DOWNLOAD = "app/trasposiciones/download"
ALLOWED_EXTENSIONS = {'ods', 'xls', 'xlsx'}
def procesar(syjArchivo,rubro0Archivo ,nAno):
    sueldos = pd.read_excel(UPLOAD_FOLDER + "/" +syjArchivo)
    sueldos['PROGRAMA'] = sueldos['PROGRAMA'].apply(lambda x: '0'+str(x))
    sueldos = sueldos.groupby(['PROGRAMA','RUBRO',]).sum('TOTAL').reset_index()
    proyectado = pd.read_excel(UPLOAD_FOLDER + "/" + rubro0Archivo,converters = {'Programa': str}, header= 9)
    proyectado = proyectado.merge(sueldos, how = 'outer' , indicator = True, left_on = ['Programa','Rubro'], right_on = ['PROGRAMA','RUBRO'])
    revisar = proyectado[proyectado['_merge'] == 'right_only']

    proyectado = proyectado[proyectado['_merge'] != 'right_only']

    proyectado['OBLIGADO'].fillna(0, inplace=True)
    proyectado['Saldo'] = proyectado.Disponible - proyectado.OBLIGADO

    negativos = proyectado[proyectado.Saldo  < 0 ]

    trasponer = pd.DataFrame(columns=('Tipo', 'Rubro','Programa','Reforzado/Reforzante' ,'Trasponer'))
    error = pd.DataFrame(columns=('Mensaje','Rubro'))
    for index, row in negativos.iterrows():
        #5063000
        if row.Rubro in (5053000 ,5063000, 5073000,5075000 ):
            #Sale de RRHH 5053000 5071000
            if (proyectado[ (proyectado.Programa == '010300') & (proyectado.Rubro == row.Rubro)].iloc[0]['Saldo'] + row.Saldo >= 0 ):
                trasponer.loc[len(trasponer)] = {'Tipo':'Entre Programas', 'Rubro':row.Rubro,'Programa' :'010300','Reforzado/Reforzante' : 'Reforzante', 'Trasponer' : row.Saldo }
                trasponer.loc[len(trasponer)] = {'Tipo':'Entre Programas','Rubro':row.Rubro,'Programa' :row.Programa,'Reforzado/Reforzante' : 'Reforzado', 'Trasponer' : -(row.Saldo) }
                proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] -  row['Saldo']
                proyectado.loc[(proyectado['Programa'] == '010300') & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == '010300') & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] + row['Saldo']


    negativos = proyectado[proyectado.Saldo  < 0 ]
    for index, row in negativos.iterrows():

        #Sale de 5011000 y 5021000
        totSBCargos = proyectado[ (proyectado.Programa == row.Programa) & (proyectado.Rubro == 5011000)].iloc[0]['Saldo']
        totSBContratados = proyectado[ (proyectado.Programa == row.Programa) & (proyectado.Rubro == 5021000)].iloc[0]['Saldo']

        porCargos = totSBCargos /(totSBCargos + totSBContratados)
        porContratados = 1 - porCargos
        if (totSBCargos *  porCargos +  totSBContratados * porContratados +  row.Saldo >= 0):
            trasponer.loc[len(trasponer)] = {'Tipo':'Dentro de Programas','Rubro':5011000,'Programa' :row.Programa,'Reforzado/Reforzante' : 'Reforzante', \
                                          'Trasponer' : round((row.Saldo) * porCargos,2)}
            trasponer.loc[len(trasponer)] = {'Tipo':'Dentro de Programas', 'Rubro':5021000,'Programa' :row.Programa,'Reforzado/Reforzante' : 'Reforzante', \
                                          'Trasponer' : round((row.Saldo) * porContratados,2)}
            trasponer.loc[len(trasponer)] = {'Tipo':'Dentro de Programas','Rubro':row.Rubro,'Programa' :row.Programa,'Reforzado/Reforzante' : 'Reforzado', \
                                          'Trasponer' : -row.Saldo}

            proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] -  row['Saldo']
            proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == '5011000'), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == '5011000'), 'Saldo']  +  round((row.Saldo) * porCargos,2)
            proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == '5021000'), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == '5021000'), 'Saldo'] +  round((row.Saldo) * porContratados,2)




    negativos = proyectado[proyectado.Saldo  < 0 ]
    for index, row in negativos.iterrows():

        #Sale de sueldos de RRHH si no hay
        totSBCargos = proyectado[ (proyectado.Programa == '010300') & (proyectado.Rubro == 5011000)].iloc[0]['Saldo']
        totSBContratados = proyectado[ (proyectado.Programa == '010300') & (proyectado.Rubro == 5021000)].iloc[0]['Saldo']

        porCargos = totSBCargos /(totSBCargos + totSBContratados)
        porContratados = 1 - porCargos
        if (totSBCargos *  porCargos +  totSBContratados * porContratados + row.Saldo >= 0):
            trasponer.loc[len(trasponer)] ={'Tipo':'Dentro de Programas','Rubro':5011000,'Programa' :'010300','Reforzado/Reforzante' : 'Reforzante', \
                                          'Trasponer' : round((row.Saldo) * porCargos,2)}
            trasponer.loc[len(trasponer)] ={'Tipo':'Dentro de Programas', 'Rubro':5021000,'Programa' : '010300','Reforzado/Reforzante' : 'Reforzante', \
                                          'Trasponer' : round((row.Saldo) * porContratados,2)}
            trasponer.loc[len(trasponer)] ={'Tipo':'Dentro de Programas','Rubro':row.Rubro,'Programa' :row.Programa,'Reforzado/Reforzante' : 'Reforzado', \
                                          'Trasponer' : -row.Saldo}
            proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == row['Rubro']), 'Saldo'] -  row['Saldo']
            proyectado.loc[(proyectado['Programa'] == '010300') & (proyectado['Rubro'] == '5011000'), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == '5011000'), 'Saldo']  +  round((row.Saldo) * porCargos,2)
            proyectado.loc[(proyectado['Programa'] ==  '010300') & (proyectado['Rubro'] == '5021000'), 'Saldo'] = proyectado.loc[(proyectado['Programa'] == row['Programa']) & (proyectado['Rubro'] == '5021000'), 'Saldo'] +  round((row.Saldo) * porContratados,2)
        else:
            error.loc[len(error)] =  {'Mensaje' : "Error " + str(int(row.Rubro)) + " " + str(row.Programa)  + " " + str(row.Saldo)}

    if len(trasponer) > 0:
        agTrasponer = trasponer.groupby(['Rubro','Programa']).sum('Trasponer').reset_index()
        aTrasponer = pd.merge(agTrasponer, proyectado,on = ['Programa','Rubro'], how = 'inner' )


        aTrasponer = aTrasponer.filter(['Rubro','Nombre.1','Programa','Nombre', 'Presupuestado' , 'Disponible','Trasponer'])
        atr = aTrasponer
        atr['ejercicio'] = nAno
        atr = atr[['ejercicio', 'Rubro','Programa','Trasponer' ]]
        for index, row in revisar.iterrows():

            error.loc[len(error)] = {'Mensaje' : "Revisar Rubro: " + str(int(row.RUBRO)) + " Programa: " + str(row.PROGRAMA)  + " " }

        shutil.copyfile(os.path.join(trasposiciones.root_path, "download/") + "PLANILLA TRASPOSICION.xlsx",os.path.join(trasposiciones.root_path, "download/") + "ATrasponer.xlsx")
        with pd.ExcelWriter(os.path.join(trasposiciones.root_path, "download/") + "ATrasponer.xlsx", mode='a',if_sheet_exists ='overlay') as writer:
            atr.to_excel( writer, sheet_name='Sheet0', startrow=8, index = False,header=False)
    else:
        shutil.copyfile(os.path.join(trasposiciones.root_path, "download/") + "PLANILLA TRASPOSICION.xlsx",os.path.join(trasposiciones.root_path, "download/") + "ATrasponer.xlsx")
        error.loc[len(error)] = {'Mensaje' : "No hay trasposiciones a realizar" }

    return error['Mensaje']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@trasposiciones.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file1' not in request.files:
            flash('Falta archivo de SYJ', 'error')
            return redirect(request.url)
        if 'file2' not in request.files:
            flash('Falta archivo de Rubro 0', 'error')
            return redirect(request.url)
        file1 = request.files['file1']
        file2 = request.files['file2']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file1.filename == '':
            flash('No seleccionó archivo de SYJ', 'error')
            return redirect(request.url)
        if file2.filename == '':
            flash('No seleccionó archivo de Rubro 0 ', 'error')
            return redirect(request.url)
        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)

            file1.save(os.path.join(UPLOAD_FOLDER, filename1))
            file2.save(os.path.join(UPLOAD_FOLDER, filename2))
            ano = request.form.get('ano')

            salida = procesar(filename1,filename2,ano)


            return render_template('trasposiciones/resultado.html', salida = salida)
        else:
            flash('Archivo no válido',  'error')
            return redirect(request.url)
    else:
        return render_template('trasposiciones/index.html', now=datetime.datetime.now())
    return ''

@trasposiciones.route('/down/pepe', methods=['GET', 'POST'])
def pepe():
    print('lala')
    return "fdfsf"

@trasposiciones.route('/download/<path:filename>', methods=['GET', 'POST'])
def download_file(filename):
    return send_from_directory(directory=os.path.join(trasposiciones.root_path, "download/"), filename=filename)
