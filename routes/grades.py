from flask import Blueprint, render_template, request, redirect, url_for
from models import Grade

# Blueprintの作成
grade_bp = Blueprint('grade', __name__, url_prefix='/grades')


@grade_bp.route('/')
def list():
    
    # データ取得
    grades = Grade.select()

    return render_template('grade_list.html', title='成績一覧', items=grades)

