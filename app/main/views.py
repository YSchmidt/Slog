from flask import render_template, flash, request, session, redirect, url_for, current_app, abort
from flask_login import current_user, login_required
from .. import db
from . import main
from ..models import User, Role, Post, Permission
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, SearchForm, CheckinForm
from ..decorators import admin_required, permission_required
from datetime import datetime


@main.route('/slog')
def slog():
    return render_template('Slog.html')


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    searchf = SearchForm()
    if searchf.validate_on_submit():
        data = searchf.req.data
        result_user = User.query.filter_by(username=data)
        result_article = Post.query.filter_by(title=data)
        postu, posts, paginationu, paginationa = None, None, None, None
        page = request.args.get('page', 1, type=int)
        if searchf.select1.data is True:
            paginationu = result_user.paginate(
                page, per_page=current_app.config['SLOG_POSTS_PER_PAGE'],
                error_out=False
            )
            postu = paginationu.items
        if searchf.select2.data is True:
            paginationa = result_article.paginate(
                page, per_page=current_app.config['SLOG_POSTS_PER_PAGE'],
                error_out=False
            )
            posts = paginationa.items
        return render_template('index.html', searchf=searchf, form=form,
                               postu=postu, paginationu=paginationu,
                               posts=posts, pagnationa=paginationa)
    elif current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data, author=current_user._get_current_object(), visible=form.visible.data)
        db.session.add(post)
        return redirect(url_for('.index'))
    else:
        result = Post.query.order_by(Post.postime.desc())
        page = request.args.get('page', 1, type=int)
        paginationa = result.paginate(
            page, per_page=current_app.config['SLOG_POSTS_PER_PAGE'],
            error_out=False
        )
        posts = paginationa.items
        return render_template('index.html', searchf=searchf, form=form, posts=posts, paginationa=paginationa)


@main.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
    checkbutton = CheckinForm()
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = Post.query.filter_by(author=user)
    #posts = posts.order_by(Post.postime.desc())
    page = request.args.get('page', 1, type=int)
    pagination = posts.paginate(
        page, per_page=current_app.config['SLOG_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    if checkbutton.validate_on_submit():
        now = datetime.utcnow()
        logtime = user.logintime
        if logtime is None:
            user.coins = 0
            user.coins += 5
            user.logintime = now
            redirect(url_for('.user', username=user.username))
        elif now.year != logtime.year or now.month != logtime.month or now.day != logtime.day:
            user.coins += 5
            redirect(url_for('.user', username=user.username))
        else:
            flash('You have checked in today!')
    return render_template('user.html', user=user, posts=posts, checkbutton=checkbutton, pagination=pagination)


@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.realname = form.realname.data
        current_user.location = form.location.data
        current_user.self_info = form.self_info.data
        db.session.add(current_user)
        flash('You have update your profile.')
        return redirect(url_for('.user', username=current_user.username))
    form.realname.data = current_user.realname
    form.location.data = current_user.location
    form.self_info.data = current_user.self_info
    return render_template('edit_profile.html', form=form)


@main.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_profile(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.role = Role.query.get(form.role.data)
        user.realname = form.realname.data
        user.location = form.location.data
        user.self_info = form.self_info.data
        db.session.add(user)
        flash('You have update this profile.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.role.data = user.role_id
    form.realname.data = user.realname
    form.location.data = user.location
    form.self_info.data = user.self_info
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>')
def post(id):
    post = Post.query.filter_by(id=id).first()
    return render_template('post.html', posts=[post])


@main.route('/article/<int:id>')
def article(id):
    post = Post.query.filter_by(id=id).first()
    return render_template('article.html', post=post)


@main.route('/edit_post/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Post.query.filter_by(id=id).first()
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.visible = form.visible.data
        db.session.add(post)
        flash('You have update this articles.')
        return redirect(url_for('.post', id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    form.visible.data = post.visible
    return render_template('edit_post.html', form=form, post=post)


@main.route('/delete_post/<int:id>', methods=['GET', 'POST'])
def delete_post(id):
    post = Post.query.filter_by(id=id).first()
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    db.session.query(Post).filter(Post.id == post.id).delete()
    db.session.commit()
    #posts = current_user.posts.order_by(Post.postime.desc()).all()
    return redirect(url_for('.index'))


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user!')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user!')
        return redirect(url_for('.index'))
    if current_user.is_following(user) is None:
        flash('You already unfollowed this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s now.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user!')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['SLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'starttime': item.starttime} for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of ",
                           endpoint='.followers', pagination=pagination, follows=follows)


@main.route('/folllowed/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def followed(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['SLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'starttime': item.starttime} for item in pagination.items]
    return render_template('followers.html', user=user, title='Followed by',
                           endpoint='.followed', pagination=pagination, follows=follows)
