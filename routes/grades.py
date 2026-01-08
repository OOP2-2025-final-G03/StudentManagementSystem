from flask import Blueprint, render_template, request, redirect, url_for, flash
from peewee import DoesNotExist
from models import Grade

# Blueprintの作成
grade_bp = Blueprint('grade', __name__, url_prefix='/grades')


@grade_bp.route('/')
def list():
    """
    成績一覧（検索・フィルタ）
    クエリ例:
      /grades/?q=K24039
      /grades/?student_number=K24039
      /grades/?subject_id=1
      /grades/?filter=pass  (score >= 60)
      /grades/?filter=fail  (score < 60)
    """

    # 検索・フィルタ
    q = (request.args.get('q') or '').strip()
    student_number = (request.args.get('student_number') or '').strip()
    subject_id_raw = (request.args.get('subject_id') or '').strip()
    current_filter = request.args.get('filter', 'all')  # all / pass / fail

    query = Grade.select()

    # フリーワード検索（学籍番号 or 科目ID）
    if q:
        if q.isdigit():
            query = query.where(Grade.subject_id == int(q))
        else:
            query = query.where(Grade.student_number.contains(q))

    # 個別検索
    if student_number:
        query = query.where(Grade.student_number.contains(student_number))

    if subject_id_raw:
        if subject_id_raw.isdigit():
            query = query.where(Grade.subject_id == int(subject_id_raw))
        else:
            flash('科目IDは数字で入力してください。', 'error')

    # 合否フィルタ（ルールは必要に応じて変更）
    if current_filter == 'pass':
        query = query.where(Grade.score >= 60)
    elif current_filter == 'fail':
        query = query.where(Grade.score < 60)

    # 表示順（学籍番号→科目ID）
    query = query.order_by(Grade.student_number.asc(), Grade.subject_id.asc())

    grades = list(query)

    # テンプレート側の変数名ブレ対策で複数渡す
    return render_template(
        'grade_list.html',
        title='成績一覧',
        items=grades,
        grades=grades,
        current_filter=current_filter
    )


@grade_bp.route('/create', methods=['GET', 'POST'])
def create():
    """
    成績登録（教師/スーパーユーザー想定）
    """
    # ここに権限チェックを入れる（例）
    # @login_required
    # @role_required(['teacher', 'superuser'])

    if request.method == 'POST':
        student_number = (request.form.get('student_number') or '').strip()
        subject_id_raw = (request.form.get('subject_id') or '').strip()
        unit_raw = (request.form.get('unit') or '').strip()
        score_raw = (request.form.get('score') or '').strip()

        # バリデーション
        if not student_number:
            flash('学籍番号を入力してください。', 'error')
            return render_template('grade_form.html', title='成績登録', mode='create')

        if not (subject_id_raw.isdigit() and unit_raw.isdigit() and score_raw.isdigit()):
            flash('科目ID / 単位 / 評価 は数字で入力してください。', 'error')
            return render_template('grade_form.html', title='成績登録', mode='create')

        subject_id = int(subject_id_raw)
        unit = int(unit_raw)
        score = int(score_raw)

        if unit < 0:
            flash('単位は0以上で入力してください。', 'error')
            return render_template('grade_form.html', title='成績登録', mode='create')

        if not (0 <= score <= 100):
            flash('評価は0〜100で入力してください。', 'error')
            return render_template('grade_form.html', title='成績登録', mode='create')

        # 重複チェック（学籍番号×科目IDが既にある場合は弾く）
        exists = Grade.select().where(
            (Grade.student_number == student_number) &
            (Grade.subject_id == subject_id)
        ).exists()
        if exists:
            flash('同じ学籍番号・科目IDの成績が既に存在します。編集してください。', 'error')
            return redirect(url_for('grade.list', student_number=student_number))

        Grade.create(
            student_number=student_number,
            subject_id=subject_id,
            unit=unit,
            score=score
        )
        flash('成績を登録しました。', 'success')
        return redirect(url_for('grade.list'))

    # GET
    return render_template('grade_form.html', title='成績登録', mode='create')


@grade_bp.route('/edit/<student_number>/<int:subject_id>', methods=['GET', 'POST'])
def edit(student_number: str, subject_id: int):
    """
    成績編集（教師/スーパーユーザー想定）
    """
    # ここに権限チェックを入れる（例）
    # @login_required
    # @role_required(['teacher', 'superuser'])

    try:
        grade = Grade.get(
            (Grade.student_number == student_number) &
            (Grade.subject_id == subject_id)
        )
    except DoesNotExist:
        flash('対象の成績が見つかりませんでした。', 'error')
        return redirect(url_for('grade.list'))

    if request.method == 'POST':
        unit_raw = (request.form.get('unit') or '').strip()
        score_raw = (request.form.get('score') or '').strip()

        if not (unit_raw.isdigit() and score_raw.isdigit()):
            flash('単位 / 評価 は数字で入力してください。', 'error')
            return render_template('grade_form.html', title='成績編集', mode='edit', grade=grade)

        unit = int(unit_raw)
        score = int(score_raw)

        if unit < 0:
            flash('単位は0以上で入力してください。', 'error')
            return render_template('grade_form.html', title='成績編集', mode='edit', grade=grade)

        if not (0 <= score <= 100):
            flash('評価は0〜100で入力してください。', 'error')
            return render_template('grade_form.html', title='成績編集', mode='edit', grade=grade)

        grade.unit = unit
        grade.score = score
        grade.save()

        flash('成績を更新しました。', 'success')
        return redirect(url_for('grade.list', student_number=student_number))

    # GET
    return render_template('grade_form.html', title='成績編集', mode='edit', grade=grade)


@grade_bp.route('/delete/<student_number>/<int:subject_id>', methods=['GET', 'POST'])
def delete(student_number: str, subject_id: int):
    """
    成績削除（教師/スーパーユーザー想定）
    ※ テンプレートが <a href="..."> のGET削除でも動くように GET も許可。
       可能ならフォームPOSTに寄せるのがおすすめ。
    """
    # ここに権限チェックを入れる（例）
    # @login_required
    # @role_required(['teacher', 'superuser'])

    try:
        grade = Grade.get(
            (Grade.student_number == student_number) &
            (Grade.subject_id == subject_id)
        )
        grade.delete_instance()
        flash('成績を削除しました。', 'success')
    except DoesNotExist:
        flash('対象の成績が見つかりませんでした。', 'error')

    return redirect(url_for('grade.list'))


