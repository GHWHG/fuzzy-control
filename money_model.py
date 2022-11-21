from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import random
from fcl import fcl

moneyRaising = fcl("fcl.txt") # create fcl object

class MoneyAgent(Agent):
    """ An agent with fixed initial wealth."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.initial_willingness = random.randint(0, 10) # higher willingness indicates higher possibility of giving more money
        self.neighbour_willingness = 0
        self.wealth = 1000

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore = True,
            include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self,new_position)

    def give_money(self):
        moneyRaising.fis_name.input['initial_willingness'] = self.initial_willingness
        moneyRaising.fis_name.input['neighbour_willingness'] = self.neighbour_willingness
        moneyRaising.fis_name.compute()
        money_out = float(moneyRaising.fis_name.output['money_out'])
        print("I give out "+ str(money_out)+"\n")
        MoneyModel.total_money += money_out # total money collected
        #cellmates = self.model.grid.get_cell_list_contents([self.pos])

    def step(self):
        # The agent's step will go here.
        # For demonstration purposes we will print the agent's unique_id
        self.move()
        cellmates = self.model.grid.get_cell_list_contents([self.pos])

        self.neighbour_willingness = 0
        for cellmate in cellmates:
            self.neighbour_willingness += cellmate.initial_willingness


        self.neighbour_willingness = self.neighbour_willingness/len(cellmates)#calculate average neighbour willingness


        print("Hi, I am agent " + str(self.unique_id) + "." + " my initial W is " + str(self.initial_willingness)
              + ", my neighbour's W is " + str(self.neighbour_willingness) )

        if self.wealth>0:
            self.give_money()


'''
model class holds the model-level attributes, manages the agents, and generally handles the global level of the model
'''
class MoneyModel(Model):
    total_money = 1
    """A model with some number of agents."""
    def __init__(self, N, width, height):
        self.num_agents = N #each model will contain multiple agents, all of which are instantiations of the agent class
        self.grid = MultiGrid(width,height,True)
        self.schedule = RandomActivation(self)

        # Create agents
        for i in range(self.num_agents):
            a = MoneyAgent(i, self) # instantiate agent class
            self.schedule.add(a) # add an agent to the schedule

            #add agents to cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a,(x,y))


    def step(self):
        '''Advance the model by one step.'''
        self.schedule.step()
        #when we call the schedule’s step method,
        #the model shuffles the order of the agents,
        #then activates and executes each agent’s step method.