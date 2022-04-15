class plant:
    coal_e = 0.36
    coal_emit = 0.26
    gas_e = 0.45
    gas_emit = 0.14
    time_grid = 10
    abatement_requirement = 0.8 #Required to decrease 20% of the total carbon emission
    def __init__(self, T, fs_price, total_demand):
        self.demand = np.zeros(T)
        self.fs_price = np.zeros(T)
        self.fs_price[0] = fs_price
        self.demand_process(total_demand)
        self.T = T
        self.total_allowance = sum(self.demand[:])*self.abatement_requirement*self.coal_emit/self.coal_e
        self.abate = np.zeros(T)

    def update_abate(self, A, t_0):
        #update abatement strategy based on the allowance price A
        for t in range(t_0, self.T):
            if A > self.fs_price[t]:
                #choose gas
                self.abate[t] = self.demand[t]*(self.coal_emit/self.coal_e - self.gas_emit/self.gas_e) #unit in GJ

    def demand_process(self, total_demand):
        #Construct demand process for each day in the period of T
        avg_demand = total_demand/(len(self.demand))
        for i in range(len(self.demand)-1):
            self.demand[i] = avg_demand*(1 + max(-1, 0.3*np.random.normal()))
        self.demand[-1] = max(0,total_demand - sum(self.demand[:-1]))

    def fs_process(self, drift, vol):
        #Construct the fuel switching process. We use log-normal distribution but could be changed to ARMA process.
        for i in range(self.T-1):
            last = self.fs_price[i]
            for j in range(self.time_grid):
                last += (last*drift*1/self.time_grid + last*vol*np.random.normal()*np.sqrt(1/self.time_grid))
            self.fs_price[i+1] = last

    def exceeded_allowance(self, t):
        #Find how much allowance we left or outstanding
        return (sum(self.demand[t:])*(1-self.abatement_requirement)*self.coal_emit/self.coal_e - sum(self.abate[t:]))

    '''
    @staticmethod
    #Could use staticmethod if we want to fix a fs_process for all the agents
    def fs_process(self, drift, vol):
        #Construct the fuel switching process. We use log-normal distribution but could be changed to ARMA process.
        for i in range(self.T-1):
            last = self.fs_price[i]
            for j in range(self.time_grid):
                last += (last*drift*1/self.time_grid + last*vol*np.random.normal()*np.sqrt(1/self.time_grid))
            self.fs_price[i+1] = last
    '''

def test(T, A, M, N, fs_price_0, total_demand, drift, vol, penalty):
    allowance = []
    agents = []
    for i in range(N):
        agents.append(plant(T, fs_price_0, total_demand[i]))
        agents[i].fs_process(drift[i], vol[i])
        agents[i].update_abate(A, 0)
    A = incompliance_p(agents, 0)*penalty
    for h in range(M):
        #iterate M times
        for i in range(N):
            #consider N agents
            agents[i].update_abate(A, 0)
        A = incompliance_p(agents, 0)*penalty
    allowance.append(A)
    for j in range(1,T):
        #from time = 1 to T
        for h in range(M):
            #iterate M times to find the equilibrium
            for i in range(N):
                #consider N agents with different demand process and different fuel switching price due to efficiency
                agents[i].update_abate(A, j)
            A = incompliance_p(agents, j)*penalty
        allowance.append(A)
    return (allowance, agents)

def incompliance_p(agents, t):
    num = 0
    for i in range(len(agents)):
        if(agents[i].exceeded_allowance(t) > 0):
            num += 1
    return num/len(agents)

T = 100
#T days to the end of compliance period
fs_price_0 = 20
#Initial Fuel Switching Price
N = 500
#500 agents
M = 10
#Iterate 10 times for each time t
total_demand = np.zeros(N)
for i in range(N):
    total_demand[i] = 1000
#Total Demand is 1000 mWh for each agent
drift = np.zeros(N)
drift += 0.03
vol = np.zeros(N)
vol += 0.2
penalty = 40
#Penalty
A_0 = 22
#Initial Allowance price
t_0 = 0

(a_l, agents) = test(T, A_0, M, N, fs_price_0, total_demand,  drift, vol, penalty)
