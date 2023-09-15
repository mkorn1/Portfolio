from flask import Flask, render_template, redirect, url_for, request, abort, flash

import os
import json

def load_projects():
    try:
        with open("static/projects.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_projects(projects):
    with open("static/projects.json", "w") as f:
        json.dump(projects, f)

import re

def sanitize_filename(filename):
    """
    This function takes in a filename and returns a sanitized version of it.
    Spaces are replaced with underscores, and non-alphanumeric characters (besides underscores and periods) are removed.
    """
    # Replace spaces with underscores
    sanitized = filename.replace(' ', '_')
    # Remove non-alphanumeric characters (besides underscores and periods)
    sanitized = re.sub(r'(?u)[^-\w.]', '', sanitized)
    return sanitized


app = Flask(__name__)
projects = load_projects()

@app.route('/')
def home():
    return render_template('index.html', projects=projects)

def protect():
    from flask import make_response
    auth = request.authorization
    if not auth or auth.username != 'kornacle' or auth.password != 'mkorn1994':
        response = make_response('Unauthorized', 401)
        response.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'
        return response
    else:
        return 'Yalla'

@app.route('/admin')
def admin():
    x = protect()
    if x == 'Yalla':
        return render_template('admin.html', projects=projects)
    else:
        return x

@app.route('/add_project', methods=['POST'])
def add_project():
    x = protect()
    if x == 'Yalla':
        title = request.form['title']
        subtitle = request.form['subtitle']
        description = request.form['description']
        embed_link = request.form['embed_link']

        # Check if the static directory exists, if not, create it
        if not os.path.exists('static'):
            os.makedirs('static')

        thumbnail_filename = None  # Default value
        if 'thumbnail' in request.files and request.files['thumbnail'].filename != '':
            thumbnail = request.files['thumbnail']
            # Sanitize the filename
            safe_filename = sanitize_filename(thumbnail.filename)
            thumbnail_filename = os.path.join("static", safe_filename)
            try:
                thumbnail.save(thumbnail_filename)
            except Exception as e:
                print(f"Error saving thumbnail: {e}")
                flash("There was an error saving the thumbnail image. Please try again.")
                return redirect(url_for('admin'))

        # Handle the uploaded HTML file
        html_file_path = None
        if 'html_file' in request.files and request.files['html_file'].filename:
            html_file = request.files['html_file']
            safe_filename = sanitize_filename(html_file.filename)
            html_file_path = os.path.join("static", safe_filename)
            html_file.save(html_file_path)

        project = {
            "id": len(projects) + 1,
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "thumbnail": thumbnail_filename if thumbnail_filename else None,  # Set to None if there's no file
            "embed_link": embed_link,
            "html_file_path": html_file_path if html_file_path else None  # Set to None if there's no file
        }
        projects.append(project)
        save_projects(projects)
        return redirect(url_for('admin'))
    else:
        return x

@app.route('/delete_project/<int:id>')
def delete_project(id):
    global projects
    projects = [p for p in projects if p['id'] != id]
    save_projects(projects)
    return redirect(url_for('admin'))

@app.route('/edit_project/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    x = protect()
    if x == 'Yalla':
        project = next((p for p in projects if p['id'] == id), None)
        if request.method == 'POST':
            project['title'] = request.form['title']
            project['subtitle'] = request.form['subtitle']
            project['description'] = request.form['description']

            if 'thumbnail' in request.files and request.files['thumbnail'].filename:
                thumbnail = request.files['thumbnail']
                safe_filename = sanitize_filename(thumbnail.filename)
                thumbnail_filename = os.path.join("static", safe_filename)
                thumbnail.save(thumbnail_filename)
                project['thumbnail'] = thumbnail_filename

            # Handle the uploaded HTML file if it exists
            if 'html_file' in request.files and request.files['html_file'].filename:
                html_file = request.files['html_file']
                safe_filename = sanitize_filename(html_file.filename)
                html_file_path = os.path.join("static", safe_filename)
                html_file.save(html_file_path)
                project['html_file_path'] = html_file_path

            project['embed_link'] = request.form['embed_link']
            save_projects(projects)
            return redirect(url_for('admin'))
        return render_template('edit.html', project=project)
    else:
        return x

@app.route('/project/<int:id>')
def project(id):
    project = next((p for p in projects if p['id'] == id), None)
    if not project:
        return "Project not found", 404  # Or redirect to a custom 404 page
    return render_template('project.html', project=project)

if __name__ == "__main__":
    app.run(debug=True)
