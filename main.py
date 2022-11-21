from money_model import *

model = MoneyModel(50,10,10) # number of agents, map width, map height

for i in range(100): # run for 100 times
  model.step()
  print(model.total_money)








