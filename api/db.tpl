<img src="/static/rxivist_logo_bad.png">
<h1>Database table visualization

% if current is not None:
	: table '{{current}}'
% end
</h1>
<strong>Available DB tables:</strong>
<ul>
	% for table in tables:
		<li><a href="/db/{{table}}">{{table}}</a></li>
	% end
</ul>
% if current is not None:
	<h2>Results</h2>
	<table border="1">
		<thead>
			<tr>
				% for header in headers:
					<th>{{header}}</th>
				% end
			</tr>
		</thead>
		<tbody>
			% for result in results:
				<tr>
					% for entry in result:
						<td>{{entry}}</td>
					% end
				</tr>
			% end
		</tbody>
	</table>
% end