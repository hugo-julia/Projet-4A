import gurobipy as gpimport pandas as pdimport numpy as npimport matplotlib.pyplot as pltfrom gurobipy import *#No of hoursh = 2190###INPUT####Hourly electricity production in 2016 (reference year)resultats_2016 = pd.read_csv("outputs/with 2016 demand/hourly profiles with demand of 2016.csv")print(resultats_2016)resultats_2016 = resultats_2016.to_numpy()vre = pd.read_csv("inputs/vre_profiles2006.csv")vre = vre.to_numpy()offshore = np.zeros((8760,2))offshore[:,1] = resultats_2016[:,1]*vre[0:8760,2]offshore[:,0] = resultats_2016[:,0]onshore = np.zeros((8760,2))onshore[:,1] = resultats_2016[:,2]*vre[8760:17520,2]onshore[:,0] = resultats_2016[:,0]PV = np.zeros((8760,2))PV[:,1] = resultats_2016[:,3]*vre[17520:26280,2]PV[:,0] = resultats_2016[:,0]river = np.zeros((8760,2))river[:,1] = resultats_2016[:,4] #*vre[26280:35040,2]river[:,0] = resultats_2016[:,0]lake = np.zeros((8760,2))lake[:,1] = resultats_2016[:,5] #*vre[35040:43800,2]lake[:,0] = resultats_2016[:,0]biogas = np.zeros((8760,2))biogas[:,1] = resultats_2016[:,6] #*vre[43800:52560,2]biogas[:,0] = resultats_2016[:,0]gas = np.zeros((8760,2))gas[:,1] = resultats_2016[:,7] #*vre[52560:61320,2]gas[:,0] = resultats_2016[:,0]prodf = np.zeros((8760,2))prodf[:,0] = resultats_2016[:,0]prodf[:,1] = offshore[:,1] + onshore[:,1]+ PV[:,1] + river[:,1] + lake[:,1] + biogas[:,1] + gas[:,1] #Electricity demand in 2050 (ADEME)#demande = pd.read_csv("inputs/demand2050_ademe_new.csv")  #demande = demande.to_numpy()##Electricity demand in 2050 (Negawatt)demande = pd.read_csv("inputs/demand2050_negawatt.csv")  demande = demande.to_numpy()#Residual productionProduction_res = np.zeros((8760,2))Production_res[:,0] = np.copy(prodf[:,0])Production_res[:,1] = prodf[:,1] - demande[:,1]#Reduced problemPR = np.zeros((h,2))PR[:,0] = Production_res[0:h,0]PR[:,1] = Production_res[0:h,1]#Residual production profileplt.plot(PR[:,1])plt.title("Residual production profile for %d hours"%h)plt.xlabel('Hours')plt.ylabel(' Hourly residual production(GWh)')plt.show()#Cost /technologya = 25.805  #phsd = 87.9481 #methanation#maximal stockxmax = 180   #valeur pour l'année 2006 (page 34, table 1.2 appendix 3)ymax = 7740 #12900#contrainte par rapport aux flux entrants et sortantRb = 6.2Db = 7.2Rm = 8Dm = 10  ### valeurs ? ???### CONSTRAINTS MATRIX ###A = np.zeros((8*h, 4*h))#contrainte de la production résiduelleI = np.eye(h)A[0:h, 0:h] = IA[0:h, h:2*h] = -IA[0:h, 2*h:3*h] = IA[0:h, 3*h:4*h] = -I#contrainte de max de stockT = np.tril(np.ones((h,h)),-1)T += IA[h:2*h, 0:h] = TA[h:2*h, h:2*h] = -TA[2*h:3*h, 2*h:3*h] = TA[2*h:3*h, 3*h:4*h] = -T#contraintes de fluxA[3*h:4*h, 0:h] = IA[4*h:5*h, h:2*h] = IA[5*h:6*h, 2*h:3*h] = IA[6*h:7*h, 3*h:4*h] = I#contraintes pour ne pas stocker ce qui n'est pas stocké#A[7*h,0:h] = -np.ones(h)#A[7*h,h:2*h] = np.ones(h)#A[7*h+1,2*h:3*h] = -np.ones(h)#A[7*h+1,3*h:4*h] = np.ones(h)#A[7*h,2*h:3*h] = -np.ones(h)#A[7*h,3*h:4*h] = np.ones(h)A[7*h:8*h, 0:h] = -TA[7*h:8*h, h:2*h] = TA[7*h:8*h, 2*h:3*h] = -TA[7*h:8*h, 3*h:4*h] = T#contrainte conservation stock (contrainte d'égalité)#E = np.zeros((1,4*h))E = np.zeros((2,4*h))E[0,0] = 1E[0,h-1] = -1E[0,h] = 1E[0,2*h-1] = -1E[0,2*h] = -1E[0,3*h-1] = 1E[0,3*h] = -1E[0,4*h-1] = 1E[1,0] = 1E[1,h] = -1E[1,2*h] = 1E[1,3*h] = -1e = np.array([0, 10])### COST FUNCTION VECTOR ###c = np.zeros((4*h,1))c[0:2*h,0] = ac[2*h:4*h,0] = dc = np.array(c)### INEQUALITY CONSTRAINT VECTOR ####b = np.zeros((7*h+2,1))#b = np.zeros((7*h+1,1))b = np.zeros((8*h,1))#prod resb[0:h,0] = Production_res[0:h,1]#max stockb[h:2*h,0] = xmax*np.ones(h)b[2*h:3*h,0] = ymax*np.ones(h)#max fluxb[3*h:4*h,0] = Rb*np.ones(h)b[4*h:5*h,0] = Db*np.ones(h)b[5*h:6*h,0] = Rm*np.ones(h)b[6*h:7*h,0] = Dm*np.ones(h)### OPTIMISATION #### Declare and initialize modelf = gp.Model('stockage')#Create variablesx = f.addMVar(shape=h*4, vtype = 'c', name="x")#Define objective functionf.setObjective(c.T @ x, GRB.MINIMIZE)#Add constraints#print(np.shape(A @ x))#print(np.shape(x))#print(np.shape(b.reshape((61322,))))f.addConstr(A @ x <= b.reshape((8*h,)), name="in")f.addConstr(E @ x == e, name="eq")f.optimize()x_res = x.X[0:h] - x.X[h:2*h]y_res = x.X[2*h:3*h] - x.X[3*h:4*h]plt.plot(x_res, c='red', linewidth = 3)plt.plot(y_res, c='purple', linewidth = 3)#plt.plot(np.cumsum(x_res+y_res), c='green', linewidth = 3)plt.plot(PR[:,1])plt.show()plt.savefig('complete_simu.png')