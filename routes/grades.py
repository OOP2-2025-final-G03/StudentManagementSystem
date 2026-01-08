from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from peewee import DoesNotExist
from config import Config
from models import Grade

# /grades/<role_type>/... に統一
grade_bp = Blueprint('grade', __name__, url_prefix='/grades/<role_type>')


@grade_bp.route('/')
def list(role_type):
    if role_type not in Config.ROLE_TITLES:
        abort(404)

    q = (request.args.get('q') or '').strip()
    current_filter = request.args.get('filter', 'all')

    query = Grade.select()

    # 検索（学籍番号 or 科目ID）
    if q:
        if q.isdigit():
            query = query.where(Grade.subject_id == int(q))
        else:
            query = query.where(Grade.student_number.contains(q))

    # 合格/不合格フィルタ（score >= 60 を合格とする）
    if current_filter == 'pass':
        query = query.where(Grade.score >= 60)
    elif current_filter == 'fail':
        query = query.where(Grade.score < 60)

    query = query.order_by(Grade.student_number.asc(), Grade.subject_id.asc())

    # list() という関数名と衝突しないよう、Pythonのlist()は呼ばずにそのまま渡す
    # ModelSelect は iterable で、テンプレの |length も動きます（countが走る）
    grades = query

    return render_template(
        'grades/grade_list.html',
        title='成績一覧',
        items=grades,
        active_template='content_base.html',
        role=role_type,       # content_base.html が role を参照するため必須
        role_type=role_type   # テンプレ内の url_for 用
    )


@grade_bp.route('/create', methods=['GET', 'POST'])
def create(role_type):
    if role_type not in Config.ROLE_TITLES:
        abort(404)

    if request.method == 'POST':
        student_number = (request.form.get('student_number') or '').strip()
        subject_id_raw = (request.form.get('subject_id') or '').strip()
        unit_raw = (request.form.get('unit') or '').strip()
        score_raw = (request.form.get('score') or '').strip()

        if not student_number:
            flash('学籍番号を入力してください。', 'error')
            return render_template(
                'grades/grade_form.html',
                title='成績登録',
                mode='create',
                active_template='content_base.html',
                role=role_type,
                role_type=role_type
            )

        if not (subject_id_raw.isdigit() and unit_raw.isdigit() and score_raw.isdigit()):
            flash('科目ID / 単位 / 評価 は数字で入力してください。', 'error')
            return render_template(
                'grades/grade_form.html',
                title='成績登録',
                mode='create',
                active_template='content_base.html',
                role=role_type,
                role_type=role_type
            )

        subject_id = int(subject_id_raw)
        unit = int(unit_raw)
        score = int(score_raw)

        # 同じ（学籍番号, 科目ID）がある場合は登録させない
        exists = Grade.select().where(
            (Grade.student_number == student_number) &
            (Grade.subject_id == subject_id)
        ).exists()
        if exists:
            flash('同じ学籍番号・科目IDの成績が既に存在します。編集してください。', 'error')
            return redirect(url_for('grade.list', role_type=role_type))

        Grade.create(student_number=student_number, subject_id=subject_id, unit=unit, score=score)
        flash('成績を登録しました。', 'success')
        return redirect(url_for('grade.list', role_type=role_type))

    return render_template(
        'grades/grade_form.html',
        title='成績登録',
        mode='create',
        active_template='content_base.html',
        role=role_type,
        role_type=role_type
    )


@grade_bp.route('/edit/<student_number>/<int:subject_id>', methods=['GET', 'POST'])
def edit(role_type, student_number, subject_id):
    if role_type not in Config.ROLE_TITLES:
        abort(404)

    try:
        grade = Grade.get(
            (Grade.student_number == student_number) &
            (Grade.subject_id == subject_id)
        )
    except DoesNotExist:
        flash('対象の成績が見つかりませんでした。', 'error')
        return redirect(url_for('grade.list', role_type=role_type))

    if request.method == 'POST':
        unit_raw = (request.form.get('unit') or '').strip()
        score_raw = (request.form.get('score') or '').strip()

        if not (unit_raw.isdigit() and score_raw.isdigit()):
            flash('単位 / 評価 は数字で入力してください。', 'error')
            return render_template(
                'grades/grade_form.html',
                title='成績編集',
                mode='edit',
                grade=grade,
                active_template='content_base.html',
                role=role_type,
                role_type=role_type
            )

        grade.unit = int(unit_raw)
        grade.score = int(score_raw)
        grade.save()

        flash('成績を更新しました。', 'success')
        return redirect(url_for('grade.list', role_type=role_type))

    return render_template(
        'grades/grade_form.html',
        title='成績編集',
        mode='edit',
        grade=grade,
        active_template='content_base.html',
        role=role_type,
        role_type=role_type
    )


@grade_bp.route('/delete/<student_number>/<int:subject_id>')
def delete(role_type, student_number, subject_id):
    if role_type not in Config.ROLE_TITLES:
        abort(404)

    try:
        grade = Grade.get(
            (Grade.student_number == student_number) &
            (Grade.subject_id == subject_id)
        )
        grade.delete_instance()
        flash('成績を削除しました。', 'success')
    except DoesNotExist:
        flash('対象の成績が見つかりませんでした。', 'error')

    return redirect(url_for('grade.list', role_type=role_type))
