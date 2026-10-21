(function(){var cb=document.getElementById('free-only');if(!cb)return;var cnt=document.getElementById('row-count');
function apply(){var n=0;document.querySelectorAll('table.filterable tbody tr').forEach(function(r){var hide=cb.checked&&r.dataset.free==='0';r.hidden=hide;if(!hide)n++;});if(cnt)cnt.textContent=n+' tools';}
cb.addEventListener('change',apply);if(new URLSearchParams(location.search).get('free')==='1'){cb.checked=true;}apply();})();
