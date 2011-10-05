Examples
########


The following is a simple one page example of using :class:`~stargate.resource.WebSocketAwareResource`
and :class:`~stargate.view.WebSocketView` with [Traversal]_ to control persistent objects in the
``resource tree``. These persistent objects communicate the control changes to connected clients
via a [WebSockets]_ connection.

.. code-block:: python
    :linenos:

    import eventlet
    from eventlet import wsgi
    from paste.httpserver import serve
    from pyramid.config import Configurator
    from pyramid.response import Response
    from pyramid.view import view_config
    from stargate import WebSocketAwareResource, WebSocketView, is_websocket
    import simplejson as json

    host = "127.0.0.1"
    port = 9999

    home_html = """\
    <html>
        <head>
            <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js"></script>
            <script>
                $(function() {
        ws = new WebSocket("ws://%(host)s:%(port)s/jobs/1/");
        ws.onmessage = function(msg) {
            $("body").append("<p>" + msg.data + "</p>");
        };
        STARTED = false;
        $("#start-stop").click(function(evt) {
            $.post("/jobs/1/", {state: STARTED ? "stop" : "start"}, function(result) {
                STARTED = !STARTED;
                $('#start-stop span').text(STARTED ? "on" : "off");

            });
        });
    });
            </script>
        </head>
        <body>
            <h1>Hi</h1>
            <button id="start-stop">Job 1 <span>off</span></button>
        </body>
    </html>
    """ % dict(host=host, port=port)

    class JobRoot(object):
        """A container for jobs

        Gets or creates Job objects for certain ids
        """

        def __init__(self):
            self._jobs = {}

        def __getitem__(self, item):
            try:
                return self._jobs[item]
            except KeyError:
                return self.create_job(item)

        def create_job(self, id):
            job = Job(id, self)
            self._jobs[id] = job
            return job


    class Job(WebSocketAwareResource):
        """This is a permanent object.

        It's responsible for maintaning a list of connected clients (websockets)
        and updating them when its state changes
        """

        def __init__(self, id, parent):
            self.__name__ = id
            self.__parent__ = parent
            self.state = "OFF"

        def control(self, state):
            """This function updates the state

            Its called by the control function (in response to a post)
            It triggers the sending of self.state to all connected clients. If you
            connect multiple browsers (or tabs) they will all be updated
            """
            self.state = state
            self.send(state)

    class JobView(WebSocketView):
        """The view connects pyramid with the resource

        In this simple example it simply adds the websocket to the Job's listeners.
        It then goes to sleep *blocking the thread it's in* this is where eventlet
        comes in. In real life you'd do things like listening for updates and
        handling messages coming in on the websocket in the while block.
        """

        def handler(self, websocket):
            job = self.request.context
            job.add_listener(websocket)
            while True:
                eventlet.sleep(60)

    def control(job, request):
        """Post to this view to set the state

        this will trigger Job to report the state to connected clients
        """
        state = request.POST.get("state")
        if state:
            job.control(state)
        return dict(id=job.__name__, state=job.state)

    class Root(dict):
        """The root of url traversal"""

        def __init__(self):
            super(Root, self).__init__(jobs=JobRoot())

    def home(request):
        """Serves up home_html, setting up a simple js demo"""
        return Response(home_html)

    root = Root()

    def root_factory(request):
        return root

    if __name__ == '__main__':
        config = Configurator(root_factory=root_factory)
        config.add_view(home, context=Root)
        config.add_view(JobView, context=Job, custom_predicates=[is_websocket])
        config.add_view(control, context=Job, renderer="json", xhr=True)
        app = config.make_wsgi_app()
        listener = eventlet.listen((host, port))
        wsgi.server(listener, app)

.. [Traversal] https://pylonsproject.org/projects/pyramid/dev/narr/traversal.html