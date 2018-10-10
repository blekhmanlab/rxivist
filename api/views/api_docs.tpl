% import helpers
<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl", google_tag=google_tag)
    <title>Rxivist privacy policy</title>
  </head>

  <body>
    <div class="container" id="main">

      %include("components/header")

      <div class="row">
        <div class="col">
          <h1>API documentation</h1>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12">
          % for chapter in docs.chapters:
            % for endpoint in chapter.endpoints:
              <h3>Endpoint: {{ endpoint.title }}</h3>
              <p>{{ endpoint.description }}<br>
              <code>{{ docs.base_url }}{{ endpoint.url }}</code></p>

              % if len(endpoint.path_arguments) + len(endpoint.get_arguments) > 0:
                <h4>Arguments</h4>
                <ul>
                  % for arg in endpoint.path_arguments + endpoint.get_arguments:
                    <li><code>{{ arg.name }}</code> &ndash; {{ arg.description }} {{ "Default: {} ".format(arg.default) if arg.default is not None else "" }}{{ "<em>Required.</em>" if arg.required else "" }}
                  % end
                </ul>
                <h4>Response</h4>
                <h4>Example</h4>
                % for example in endpoint.examples:
                  <h5>{{ example.title }}</h5>
                  <p>{{ example.description }}<br>
                  <code>{{ docs.base_url }}{{ example.url }}</code></p>
                  <h6>Response:</h6>
                  <pre>
{{ example.response }}
                  </pre>
                %end

            % end
          % end
        </div>
      </div>
    </div>

    %include("components/footer")

  </body>
</html>