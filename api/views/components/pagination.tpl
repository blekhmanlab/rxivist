% if page > 0:
  <a href="{{pagelink}}{{ page - 1 }}" class="btn btn-altcolor">Previous page</a>
% end

% if page > 1:
  <a class="pagenum" href="{{pagelink}}{{ page - 2 }}" class="btn btn-altcolor">{{ page - 2 }}</a>
% end
% if page > 0:
  <a class="pagenum" href="{{pagelink}}{{ page - 1 }}" class="btn btn-altcolor">{{ page - 1 }}</a>
  <span class="pagenum"><strong>{{ page }}</strong></span>
% end

% maxpages = 5
% page_nums_printed = 0
% for i in range(1, maxpages):
  % if (page + i) * page_size < totalcount:
    <a class="pagenum" href="{{pagelink}}{{ page + i }}" class="btn btn-altcolor">{{ page + i }}</a>
    % page_nums_printed += 1
  % end
% end

% if (page + page_nums_printed) * page_size < totalcount: # if the last page isn't the last page
  % lastpage = int(totalcount / page_size) - 1

  % if page + page_nums_printed + 1  < lastpage: # if there's a gap before the last page number
    <span class="pagenum">. . .</span>
  % end
  <a class="pagenum" href="{{pagelink}}{{ lastpage }}" class="btn btn-altcolor">{{ lastpage }}</a>
% end

% if (page + 1) * page_size < totalcount:
  <a href="{{pagelink}}{{ page + 1 }}" class="btn btn-altcolor">Next page</a>
% end