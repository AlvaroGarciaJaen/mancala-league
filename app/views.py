# -*- coding: utf-8 -*-

import os
import logging
from app import app, league, utilities
from app.constants import BOTS_FOLDER, UPLOAD_FOLDER
from werkzeug import secure_filename
from flask import render_template, request, Blueprint
from app.utilities import render_dataframe


bp = Blueprint('bp', __name__)


def alert_page(title, content):
    return render_template('page.html', title=title, content=content)


@bp.route('/subirbot')
def subirbot():
    return render_template('upload.html')


@bp.route("/")
def index():
    try:
        (exec_date, ranking, matches) = league.get_current_data()
        ranking_render = render_dataframe(ranking, 'ranking')
        matches_render = render_dataframe(matches, 'matches')
        return render_template('liga.html', tables=[ranking_render, matches_render],
                               titles=['na', 'Ranking', 'Partidos'],
                               exec_date=exec_date)
    except FileNotFoundError as ex:
        logging.error(ex)
        return alert_page('No hay datos', """No existen datos actuales de la liga.
                Ejecuta la competición en /ejecutar""")


@bp.route("/ejecutar1234")
def ejecutar():
    if league.run_competition(block_thread=False):
        return alert_page('Ejecutando competicion',
                          'Ejecutando competición... en unos minutos se actualizarán los resultados')
    else:
        return alert_page('Competicion en curso',
                          'Competición en curso, espera a que termine para ejecutar otra.')


@bp.route('/lista')
def lista():
    return render_template('lista.html', bot_list=os.listdir(BOTS_FOLDER))


@bp.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("file[]")
    cond1 = len(uploaded_files) == 2
    cond2 = all(utilities.allowed_file(x.filename) for x in uploaded_files)
    cond3 = all(not os.path.exists(os.path.join(UPLOAD_FOLDER, x.filename))
                for x in uploaded_files)
    if not (cond1 and cond2 and cond3):
        return alert_page('Error',
                          'Sube únicamente los archivos .h y .cpp de tu bot')
    filenames = []
    for file in uploaded_files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        filenames.append(filename)
    if utilities.compile_bot(filenames):
        return alert_page('Completado', 'Bot compilado con exito.')
    else:
        return alert_page('Error', 'No se puede compilar el bot')


@bp.route('/ejecutar_partido/', methods=['POST'])
def ejecutar_partido():
    bot1 = request.form.get('bot1_select')
    bot2 = request.form.get('bot2_select')
    file1 = os.path.join(BOTS_FOLDER, bot1)
    file2 = os.path.join(BOTS_FOLDER, bot2)
    if os.path.isfile(file1) and os.path.isfile(file2):
        m = league.run_match(file1, file2)
        t = render_dataframe(league.create_matches_table([m]), 'ranking')
        return render_template('liga.html', tables=[t], titles=['na', 'Partido'])
    else:
        return alert_page('Error','No existen los bots seleccionados')


@bp.route('/partido/')
def partido():
    bot_list = os.listdir(BOTS_FOLDER)
    return render_template('partido.html', bot_list=bot_list)
