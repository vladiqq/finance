select sum(amount)
from expense where
date(created)=date('now', 'localtime') 
