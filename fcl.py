import re
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

var_dict={}
'''
dictionary to store (fuzzy variable name:variable object) pairs
dictionary example: {"input_variable_name" : Scikit_fuzzy Antecedent object, 
                      "output_variable_name" : Scikit_fuzzy Consequent object...}
'''

input_variables = []
'''
list to store input variables and its information
list example: ["variable_name",[min,max],["term_name","MF_function_type",a,b,c],...,["term_name","MF_function_type",j,k,l]]
'''


output_variables = []
'''
list to store input variables and its information
list example: ["variable_name",[min,max],["term_name","MF_function_type",a,b,c],...,["term_name","MF_function_type",j,k,l]]
'''


rule_list = []
'''
convert plain text rule to list objects, and store in a list
[['RULE1', "var_dict['service']['poor']", '&', "var_dict['food']['rancid']", ',', "var_dict['tip']['cheap']"], 
 ['RULE2', "var_dict['service']['good']", ',', "var_dict['tip']['average']"]
'''

rule_objects =[]
'''
stores actual scikit-fuzzy rule object 
'''



class fcl():

    def __init__(self,file_name):
        self.file_name = file_name

        self.fis_name = None
        self.get_fis_name()
        self.get_input_var()
        self.get_output_var()
        self.get_fuzzify_terms()
        self.get_defuzzify_terms()
        self.get_rule_block()
        self.generate_fis_inputs()
        self.generate_fis_outputs()
        self.generate_membership_functions()
        self.generate_rules()

        fis_ctrl = ctrl.ControlSystem(rule_objects)
        self.fis_name = ctrl.ControlSystemSimulation(fis_ctrl)


    def get_fis_name(self):

        with open(self.file_name) as infile:
            for line in infile:
                if re.search("^FUNCTION_BLOCK", line):
                    self.fis_name = line.split("FUNCTION_BLOCK")[1].strip()
                    if len(self.fis_name) == 0: # if fis name is not defined then set it to None
                        raise Exception("FIS name not defined")

    def get_input_var(self):
        # get all input variables from VAR_INPUT block
        # and store in input_variables list
        file = open(self.file_name)
        copy = False
        for line in file:
            if re.search("VAR_INPUT", line): # locate VAR_INPUT
                copy = True
                continue
            elif re.search("END_VAR", line):
                copy = False
                continue
            elif copy:
                # when you are in VAR_INPUT block, then add current variable to input_variables list
                # append [variable name] + [variable range] to input_variables list
                input_variables.append([line.strip().split(':')[0].strip()] + [[]])


    def get_output_var(self):
        # get all ioutput variables from VAR_OUTPUT block
        # and store in output_variables list
        file = open(self.file_name)
        copy = False
        for line in file:
            if re.search("VAR_OUTPUT",line): # locate VAR_OUTPUT
                copy = True
                continue
            elif re.search("END_VAR",line):
                copy = False
                continue
            elif copy:
                # when you are in VAR_OUTPUT block, then add current variable to output_variables list
                # append [variable name] + [variable range] to output_variables list
                output_variables.append([line.strip().split(':')[0].strip()]+[[]])
                #line.strip() removes leading and trailing space
                #line.strip().split(':') divide the line into two parts from the position ':'
                #line.strip().split(':')[0] take the first part


    def get_fuzzify_terms(self):
        # get all terms from FUZZIF block
        with open(self.file_name) as infile:
            copy = False
            for line in infile:
                if re.search("^FUZZIFY",line): # locate fuzzify block
                    copy = True
                    try:
                        line = line.replace(" ", "") #remove all space
                        line = line.replace("FUZZIFY", "FUZZIFY ") # no error will be raised if the user forgets to add a space
                        var_name = line.split()[1].strip() # each FUZZIFY block corresponds to one variable, so variable name is required
                    except:
                        raise Exception("input variable name not defined")
                elif re.search("^END_FUZZIFY",line):
                    copy = False
                    continue
                elif copy:
                    if re.findall("TERM",line): # get each term
                        term_name = line.split(":=")[0].split()[1] # get term name
                        term = self.get_mf_configuration(line, term_name)  # get mf configuration
                        self.add_to_input_var_list(term, var_name) # add current term and its configuration to the input_variables list

            for variable in input_variables:    # get min and max value for variable
                min = float(variable[2][2])
                max = float(variable[-1][-1])+1  # +1 because np.arange does not include the last value
                variable[1].append(min)
                variable[1].append(max)

    def get_defuzzify_terms(self):
        with open(self.file_name) as infile:
            copy = False
            for line in infile:
                if re.search("^DEFUZZIFY",line):
                    copy = True
                    try:
                        line = line.replace(" ", "") #remove all space
                        line = line.replace("FUZZIFY", "FUZZIFY ")
                        var_name = line.split(" ")[1].strip()
                    except:
                        raise Exception("output variable name not defined")
                        break
                elif re.search("^END_DEFUZZIFY",line):
                    copy = False
                    continue
                elif copy:
                    if re.findall("TERM", line):  # get each term
                        term_name = line.split(":=")[0].split()[1]
                        term = self.get_mf_configuration(line, term_name)  # mf configuration
                        self.add_to_output_var_list(term, var_name)
            for variable in output_variables:  # get min and max value for variable
                min = float(variable[2][2])
                max = float(variable[-1][-1])+1  # +1 because np.array does not include last value
                variable[1].append(min)
                variable[1].append(max)


    def get_mf_configuration(self,line,term_name):
        # get MF type and points that define the MF
        if re.search("piece",line):
            config = line.replace("("," ").replace(")"," ").replace(","," ").split(";")[0].split("piece")[1].split()
        else:
            config = line.replace("("," ").replace(")"," ").replace(","," ").split(";")[0].split(":=")[1].split()
            del config[1::2] # Remove odd-indexed elements from list, which is the membership degree value
        if re.findall("piece", line):
            config.insert(0, "piece")
        elif len(config) == 3:
            config.insert(0, "tri")
        elif len(config) == 4:
            config.insert(0,"trap")
        config.insert(0, term_name)
        return config


    def add_to_input_var_list(self,config,var_name):
        #add term confirguration to variable list
        for i in range(len(input_variables)):
            if input_variables[i][0] == var_name:
                #[variable_name,[min,max],[config],[config]]
                input_variables[i] = input_variables[i] + [config]

    def add_to_output_var_list(self,config,var_name):
        for i in range(len(output_variables)):
            if output_variables[i][0] == var_name:
                output_variables[i] = output_variables[i] + [config]

    def get_rule_block(self):
        with open(self.file_name) as infile:
            copy = False
            for line in infile:
                if re.search("^RULEBLOCK",line):
                    copy = True
                    try:
                        rule_block_name = line.split(" ")[1].strip()
                    except:
                        rule_block_name = "NOT DEFINED"
                elif re.search("^END_RULEBLOCK",line):
                    copy = False
                    continue
                elif copy:
                    rule = []
                    if re.search("RULE",line):
                        rule_name = line.strip().split(":")[0].replace(" ","")
                        rule.append(rule_name)
                        if re.search("[(]",line) and re.search("NOT",line) and re.search("[)]",line):#
                            line = line.replace("("," ( ")
                            line = line.replace(")"," ) ")
                        temp = line.split(";")[0].split(":")[1].strip().split("IF")[1].strip().split()
                        for i in range(len(temp)):
                            if temp[i] == "IS":
                                if temp[i+1] == "NOT":
                                    rule.append("~var_dict"+"['"+temp[i-1]+"']"+"['"+temp[i+2]+"']")
                                elif temp[i-2] == "(" and temp[i+2] == ")":
                                    pass
                                else:
                                    rule.append("var_dict"+"['"+temp[i-1]+"']"+"['"+temp[i+1]+"']")
                            elif temp[i] == "AND":
                                rule.append('&')
                            elif temp[i] == "OR":
                                rule.append('|')
                            elif temp[i] =="THEN":
                                rule.append(",")
                            elif temp[i] == "NOT" and temp[i+1] =="(":
                                rule.append("~var_dict"+"['"+temp[i+2]+"']"+"['"+temp[i+4]+"']")
                        rule_list.append(rule)







    ############################################################################################
    def generate_fis_inputs(self):
        # calling sickit function
        for variable in input_variables:
            name = variable[0]
            variable[0] = ctrl.Antecedent(np.arange(float(variable[1][0]), float(variable[1][1]), 1), variable[0])
            var_dict[name] = variable[0]

    def generate_fis_outputs(self):
        # calling sickit function
        for variable in output_variables:
            #variable name = ctrl.Consequent(np.arange(min, max, weight),fuzzy variable name)
            name = variable[0]
            variable[0] = ctrl.Consequent(np.arange(float(variable[1][0]), float(variable[1][1]), 1), variable[0])
            var_dict[name] = variable[0]

    def generate_membership_functions(self):
        # loop through all the input variables
        print(input_variables)
        for variable in input_variables:
            for i in range(2,len(variable)): # loop through each variable and its configurations, index 2 and after are mf configurations
                if variable[i][1] == "tri": # variable[i][1] is mf type
                    # variable[0] is the variable name
                    # variable[i][0] is the term name
                    # float(variable[i][2]), float(variable[i][3]), float(variable[i][4]) are 3 parameters that defines triangular mf
                    # example function call: var_name['term_name'] = fuzz.trimf(var_name.universe, [a, b, c])
                    variable[0][variable[i][0]] = fuzz.trimf(variable[0].universe,[float(variable[i][2]),float(variable[i][3]),float(variable[i][4])])
                if variable[i][1] == "trap":
                    variable[0][variable[i][0]] = fuzz.trapmf(variable[0].universe,[float(variable[i][2]),float(variable[i][3]),float(variable[i][4]),float(variable[i][5])])
                if variable[i][1] == "piece":
                    variable[0][variable[i][0]] = fuzz.trimf(variable[0].universe,[float(variable[i][2]), float(variable[i][3]),float(variable[i][4])])
            #variable[0][] = fuzz.trimf(variable[0].universe,[])

        # loop through all the output variables
        for variable in output_variables:
            for i in range(2,len(variable)): # loop through each variable and its configurations, index 2 and after are mf configurations
                if variable[i][1] == "tri": # variable[i][1] is mf type
                    # variable[0] is the variable name
                    # variable[i][0] is the term name
                    # float(variable[i][2]), float(variable[i][3]), float(variable[i][4]) are 3 parameters that defines triangular mf
                    # example function call: var_name['term_name'] = fuzz.trimf(var_name.universe, [a, b, c])
                    variable[0][variable[i][0]] = fuzz.trimf(variable[0].universe,[float(variable[i][2]),float(variable[i][3]),float(variable[i][4])])
                if variable[i][1] == "trap":
                    variable[0][variable[i][0]] = fuzz.trapmf(variable[0].universe,[float(variable[i][2]),float(variable[i][3]),float(variable[i][4]),float(variable[i][5])])
                if variable[i][1] == "piece":
                    variable[0][variable[i][0]] = fuzz.trimf(variable[0].universe,[float(variable[i][2]), float(variable[i][3]),float(variable[i][4])])
    def generate_rules(self):
        for rule in rule_list:
            input_string = ""
            for i in range(1, len(rule)):
                input_string = input_string + rule[i]
            r = eval('ctrl.Rule({})'.format(input_string))
            rule_objects.append(r)







