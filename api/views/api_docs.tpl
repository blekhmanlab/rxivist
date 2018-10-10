% import helpers
% accordion_count = 0

<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl", google_tag=google_tag)
    <title>Rxivist API Documentation</title>
  </head>

  <body>
    <div class="container" id="main">

      %include("components/header")

      <div class="row">
        <div class="col-sm-12">
          <h1>API documentation</h1>
        </div>
        <div class="col-sm-10 offset-sm-1">
          <p>The Rxivist API offers free, programmatic access to all of our bioRxiv metadata in a RESTful JSON interface. It's open to all&mdash;no keys or authentication here, at least for now. We only ask that you go easy on the requests, as this is a small project with limited funding for server infrastructure.

          <p>If you are looking for data to use offline somewhere, there's no need to send 40,000 API requests to get all the data: <strong>We generate weekly database dumps that contain all Rxivist data,</strong> and you're welcome to download them. Not only is that easier for our servers to handle, but it's probably much easier for you too. The PostgreSQL dumps are available <a href="*tk">for direct download</a>.
        </div>
      </div>
      <div class="row">
        <div class="col-md-12">
          % for chapter in docs.chapters:
            <h2 style="padding-top: 20px;">{{ chapter.title }}</h2>
            <div class="col-sm-10 offset-sm-1">
              % for endpoint in chapter.endpoints:
                <h3>Endpoint: {{ endpoint.title }}</h3>
                <p>
                % if endpoint.description != "":
                  {{ endpoint.description }}<br>
                % end
                <code>{{ docs.base_url }}{{ endpoint.url }}</code></p>

                % if len(endpoint.path_arguments) + len(endpoint.get_arguments) > 0:
                  <h4>Arguments</h4>
                  <ul>
                    % for arg in endpoint.path_arguments + endpoint.get_arguments:
                      <li><code>{{ arg.name }}</code> &ndash; {{ arg.description }} {{ "Default: {} ".format(arg.default) if arg.default is not None else "" }}{{ "<em>Required.</em>" if arg.required else "" }}
                    % end
                  </ul>
                %end
                <h4>Example</h4>
                % for i, example in enumerate(endpoint.examples):
                  <h5>{{ example.title }}</h5>
                  <p>
                  % if example.description != "":
                    {{ example.description }}<br>
                  % end
                  <a href="{{ docs.base_url }}{{ example.url }}" target="_blank"><code>{{ docs.base_url }}{{ example.url }}</code></a></p>
                  <div class="accordion" id="accordion{{ accordion_count }}">
                    <div class="card">
                      <div class="card-header context" id="heading{{ accordion_count }}"  data-toggle="collapse" data-target="#collapse{{ accordion_count }}" aria-expanded="true" aria-controls="collapse{{ accordion_count }}">
                        <h6>Response:</h6>
                      </div>
                      <div id="collapse{{ accordion_count }}" class="collapse" aria-labelledby="heading{{ accordion_count }}" data-parent="#accordion{{ accordion_count }}">
                        <div class="card-body">
                          <pre>{{ example.response }}</pre>
                        </div>
                      </div>
                    </div>
                  </div>
                  % accordion_count += 1
                %end
                <hr>
              % end
            </div>
          % end
        </div>
      </div>
    </div>

    %include("components/footer")

  </body>
</html>