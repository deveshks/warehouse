# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import shlex

from paginate_sqlalchemy import SqlalchemyOrmPage as SQLAlchemyORMPage
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPMovedPermanently,
)
from pyramid.view import view_config
from sqlalchemy import or_

from warehouse.accounts.models import User
from warehouse.packaging.models import Project, Release, Role, JournalEntry
from warehouse.utils.paginate import paginate_url_factory


@view_config(
    route_name="admin.project.list",
    renderer="admin/projects/list.html",
    permission="admin",
    uses_session=True,
)
def project_list(request):
    q = request.params.get("q")

    try:
        page_num = int(request.params.get("page", 1))
    except ValueError:
        raise HTTPBadRequest("'page' must be an integer.") from None

    projects_query = request.db.query(Project).order_by(Project.name)

    if q:
        terms = shlex.split(q)

        filters = []
        for term in terms:
            filters.append(Project.name.ilike(term))

        projects_query = projects_query.filter(or_(*filters))

    projects = SQLAlchemyORMPage(
        projects_query,
        page=page_num,
        items_per_page=25,
        url_maker=paginate_url_factory(request),
    )

    return {"projects": projects, "query": q}


@view_config(route_name="admin.project.detail",
             renderer="admin/projects/detail.html",
             permission="admin",
             uses_session=True,
             require_csrf=True,
             require_methods=False)
def project_detail(project, request):
    project_name = request.matchdict["project_name"]

    if project_name != project.normalized_name:
        raise HTTPMovedPermanently(
            request.current_route_path(
                project_name=project.normalized_name,
            ),
        )

    maintainers = [
        role
        for role in (
            request.db.query(Role)
            .join(User)
            .filter(Role.project == project)
            .distinct(User.username)
            .all()
        )
    ]
    maintainers = sorted(
        maintainers,
        key=lambda x: (x.role_name, x.user.username),
    )
    journal = [
        entry
        for entry in (
            request.db.query(JournalEntry)
            .filter(JournalEntry.name == project.name)
            .order_by(JournalEntry.submitted_date.desc())
            .limit(50)
        )
    ]

    return {"project": project, "maintainers": maintainers, "journal": journal}


@view_config(
    route_name="admin.project.releases",
    renderer="admin/projects/releases_list.html",
    permission="admin",
    uses_session=True,
)
def releases_list(project, request):
    q = request.params.get("q")
    project_name = request.matchdict["project_name"]

    if project_name != project.normalized_name:
        raise HTTPMovedPermanently(
            request.current_route_path(
                project_name=project.normalized_name,
            ),
        )

    try:
        page_num = int(request.params.get("page", 1))
    except ValueError:
        raise HTTPBadRequest("'page' must be an integer.") from None

    releases_query = (request.db.query(Release)
                      .filter(Release.project == project)
                      .order_by(Release._pypi_ordering.desc()))

    if q:
        terms = shlex.split(q)

        filters = []
        for term in terms:
            if ":" in term:
                field, value = term.split(":", 1)
                if field.lower() == "version":
                    filters.append(Release.version.ilike(value))

        releases_query = releases_query.filter(or_(*filters))

    releases = SQLAlchemyORMPage(
        releases_query,
        page=page_num,
        items_per_page=25,
        url_maker=paginate_url_factory(request),
    )

    return {
        "releases": releases,
        "project": project,
        "query": q,
    }


@view_config(
    route_name="admin.project.journals",
    renderer="admin/projects/journals_list.html",
    permission="admin",
    uses_session=True,
)
def journals_list(project, request):
    q = request.params.get("q")
    project_name = request.matchdict["project_name"]

    if project_name != project.normalized_name:
        raise HTTPMovedPermanently(
            request.current_route_path(
                project_name=project.normalized_name,
            ),
        )

    try:
        page_num = int(request.params.get("page", 1))
    except ValueError:
        raise HTTPBadRequest("'page' must be an integer.") from None

    journals_query = (request.db.query(JournalEntry)
                      .filter(JournalEntry.name == project.name)
                      .order_by(JournalEntry.submitted_date.desc()))

    if q:
        terms = shlex.split(q)

        filters = []
        for term in terms:
            if ":" in term:
                field, value = term.split(":", 1)
                if field.lower() == "version":
                    filters.append(JournalEntry.version.ilike(value))

        journals_query = journals_query.filter(or_(*filters))

    journals = SQLAlchemyORMPage(
        journals_query,
        page=page_num,
        items_per_page=25,
        url_maker=paginate_url_factory(request),
    )

    return {"journals": journals, "project": project, "query": q}