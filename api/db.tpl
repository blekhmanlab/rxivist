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