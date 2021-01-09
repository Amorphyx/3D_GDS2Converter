# XS_INPUT= 

#XSection Window Setup (um)
depth(100.0) 							#Function call that is empty in code (not used)
height(100.0) 							#Function call that is empty in code (not used)
delta(1 * dbu) 							#Function call that is empty in code (not used)

#Layer Setup
substrate = bulk 						#This is a function call used in code 
m1 = layer("2/0")						#This is a function call used in code
i1 = layer("3/0")
m2 = layer("4/0")
i2 = layer("6/0")
s1 = layer("5/0") 						
m3 = layer("7/0")
m4 = layer("8/0")
i3 = layer("9/0")

#Layer CD Setup							#Bias values - variables		
s1_cdbias = 0
m1_cdbias = 0
i1_cdbias = 0
m2_cdbias = 0
i2_cdbias = 0
m3_cdbias = -1
m4_cdbias = 0
i3_cdbias = 0

#Layer % Overetch Setup
s1_overetch = 0
m1_overetch = 0
i1_overetch = 0
m2_overetch = 0
i2_overetch = 0
m3_overetch = 0
m4_overetch = 0
i3_overetch = 0

#Layer thicknesses and universal scaling factor (um)
scaling = 1
s1_nominal_t = 1
m1_nominal_t = 1
i1_nominal_t = 1
m2_nominal_t = 1
i2_nominal_t = 1
m3_nominal_t = 1
m4_nominal_t = 1
i3_nominal_t = 1


#Layer Etch Rate Anisotropy Factors, 1 = no anisotropy
s1_rate = 1
m1_rate = 1
i1_rate = 1
m2_rate = 1
i2_rate = 1
m3_rate = 1
m4_rate = 1



#Etch and Deposit Setup	(Not required)		#Calculates total bias and thicknesses
s1_xsec_t = s1_nominal_t * scaling
s1_bias = -1 * s1_cdbias

s1_etching = s1_xsec_t + (s1_overetch * s1_xsec_t)

m1_xsec_t = m1_nominal_t * scaling
m1_bias = -1 * m1_cdbias

m1_etching = m1_xsec_t + (m1_overetch * m1_xsec_t)

i1_xsec_t = i1_nominal_t * scaling
i1_bias = -1 * i1_cdbias

i1_etching = i1_xsec_t + (i1_overetch * i1_xsec_t)

m2_xsec_t = m2_nominal_t * scaling
m2_bias = -1 * m2_cdbias

m2_etching = m2_xsec_t + (m2_overetch * m2_xsec_t)

i2_xsec_t = i2_nominal_t * scaling
i2_bias = -1 * i2_cdbias

i2_etching = i2_xsec_t + (i2_overetch * i2_xsec_t)

m3_xsec_t = m3_nominal_t * scaling
m3_bias = 1 * m3_cdbias

m3_etching = m3_xsec_t + (m3_overetch * m3_xsec_t)

m4_xsec_t = m4_nominal_t * scaling
m4_bias = -1 * m4_cdbias

m4_etching = m4_xsec_t + (m4_overetch * m4_xsec_t)

i3_xsec_t = i3_nominal_t * scaling
i3_bias = -1 * i3_cdbias

i3_etching = i3_xsec_t + (i3_overetch * i3_xsec_t)





#Perform Deposit and Etch Steps
m1_dep = deposit(m1_xsec_t)
mask(m1.inverted).etch(m1_etching, :taper => 45, :bias => m1_bias, :into => m1_dep)

i1_dep = deposit(i1_xsec_t)

m2_dep = deposit(m2_xsec_t)
mask(m2.inverted).etch(m2_etching, :taper => 45, :bias => m2_bias, :into => m2_dep)  

i2_dep = deposit(i2_xsec_t)

s1_dep = deposit(s1_xsec_t)
mask(s1.inverted).etch(s1_etching, :taper => 45, :bias => s1_bias, :into => s1_dep)

m3_dep = deposit(m3_xsec_t) 
mask(m3).etch(m3_etching, :taper => 35, :bias => m3_bias, :into => m3_dep)  

m4_dep = deposit(m4_xsec_t)	
mask(m4.inverted).etch(m4_etching, :taper => 45, :bias => m4_bias, :into => m4_dep)	

i3_dep = deposit(i3_xsec_t)
planarize(:into => i3_dep, :less => 3)



#Assign the output layers
output("5/0", s1_dep) 					#This is a function call not used in code
output("2/0", m1_dep)
output("3/0", i1_dep)
output("4/0", m2_dep)
output("6/0", i2_dep)
output("7/0", m3_dep)
output("8/0", m4_dep)
output("9/0", i3_dep)
