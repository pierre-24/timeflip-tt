import flask
from flask import jsonify, Response
from flask.views import MethodView

from timefliptt.blueprints.api.views import blueprint
from timefliptt.blueprints.api.schemas import HistoryElementSchema, Parser
from timefliptt.blueprints.base_models import HistoryElement


parser = Parser()


class HistoriesView(MethodView):

    PAGE_SIZE = 5

    def get(self) -> Response:
        """Get the list of history elements
        """

        try:
            page = int(flask.request.args.get('page', 0))
            page_size = int(flask.request.args.get('page_size', self.PAGE_SIZE))
        except ValueError:
            flask.abort(422)

        num_results = HistoryElement.query.count()

        if page < 0 or page * page_size > num_results:
            flask.abort(404)

        results = HistoryElement\
            .query\
            .order_by(HistoryElement.id.desc())\
            .slice(page * page_size, (page + 1) * page_size)\
            .all()

        FORMAT = '{}?page={}&page_size={}'

        previous_page = None
        if page > 0:
            previous_page = FORMAT.format(flask.url_for('api.histories'), page - 1, page_size)
        next_page = None
        if (page + 1) * page_size < num_results:
            next_page = FORMAT.format(flask.url_for('api.histories'), page + 1, page_size)

        return jsonify(
            total=num_results,
            previous_page=previous_page,
            next_page=next_page,
            history=HistoryElementSchema(many=True).dump(results)
        )


blueprint.add_url_rule('/api/history/', view_func=HistoriesView.as_view('histories'))
