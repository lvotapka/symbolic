#!/usr/bin/python

# by Lane Votapka
# 2016

'''
A symbolic math engine that can perform differentiation, some integration, and
other analytic calculations

Features:
- Given an algebraic expression, can parse it into various forms (algebra.py)
- Given a function, can compute a derivative with respect to a variable

- Relations: I want to be able to input relations to help with traversing
  reason trees

Ideas:
 - a list of priorities of operators, put into a dictionary for the collapse() function and writing strings
 - In the next version, Operator should be changed to Expression, and operator should be reserved for characters representing operations
 - Add function-like operators for unusual ops with 0 to inf. arguments

'''

import math, re
from copy import deepcopy

simplifications = [ # we can assume that these commute
'a + 0', 'a',
'0 + a', 'a',
'a * 1', 'a',
'1 * a', 'a', # TODO: use laws of algebra to negate the need for this
'a * 0', '0',
'0 * a', '0', # TODO: use laws of algebra to negate the need for this
'a^1', 'a',
'a^0', '1',

]

laws_of_algebra = [
'a + b', 'b + a', # commutative property of addition
'a * b', 'b * a', # commutative property of multiplication   
]

# idea: expression classes that point to further expression classes        
class Variable(): # leaves on the tree
    def __init__(self, value=None):
        self.name = value

    def __str__(self):
        return self.name

    def collapse(self):
        '''return a string representation of myself'''
        return self.name
    
    def simplify(self, dummy_arg):
        return self

class Operator(): # forks in the tree
    def __init__(self, operator=None, children=[]):
        self.name = operator
        self.children = []
        for child in children:
            self.children.append(deepcopy(child))
        self.str = ''

    def __getitem__(self, key):
        return self.children[key]

    def __str__(self):
        return self.name

    def collapse(self):
        '''Reduce this operator to a string representation of itself'''
        collapsed_children = [] # creepy name
        #print "collapsing operator:", self.name
        for child in self.children:
            #print "collapsing child:", child.name
            collapsed_children.append(child.collapse())
        self.str = '(' + self.name.join(collapsed_children) + ')'
        return self.str
      
    def simplify(self, simplifications): 
        '''simplify the expression by using simplification relations specified in the 'simplifications' list'''
        new_children = []
        all_variables = True
        
        if isinstance(self, Operator): 
            for child in self.children: # loop thru the children of this expression
                new_child = child.simplify(simplifications) # do again recursively
                if isinstance(new_child, Operator):
                    all_variables = False # all children are not variables
                ''' # REMOVE
                    for simpl in simplifications: # run through the possible simplifications
                        comparison = simpl.compare(new_child) # see whether the two expressions compare
                        if comparison: # if they compare
                            new_child = comparison # then modify this operator to include the simplification
                        else:
                            new_child = new_child # otherwise, stay with the old expr
                '''
                new_children.append(new_child)
            self.children = new_children
            for simpl in simplifications: # run through the possible simplifications
                comparison = simpl.compare(self) # see whether the two expressions compare
                if comparison: # if they compare
                    self = comparison # then modify this operator to include the simplification
                    
        else:
            pass # because you cannot just simplify a variable
        
        '''
        # OLD: REMOVE
        
        for child in self.children:
            if isinstance(child, Operator): # then there is an operator in there
                new_child = child.simplify(simplifications)
                
                if isinstance(new_child, Variable):
                    pass
                else:
                    all_variables = False
                    for simpl in simplifications: # run through the possible simplifications
                        comparison = simpl.compare(child) # see whether the two expressions compare
                        if comparison:
                            new_child = comparison
                        else:
                            new_child = child
                        
                new_children.append(new_child)
            else:
                new_children.append(child)
            
                
        self.children = new_children
        #self.str = ''
        '''
        
        if all_variables: # if the children are all variables
            my_str = self.collapse()
            #print "my_str:", my_str
            if not re.search('[a-zA-Z_]', my_str): # if we don't find a letter in the string
                my_str = re.sub('\^', '**', my_str) # replace the power operator with a form Python will understand
                simplification = str(eval(my_str)) # evaluate this operation
                #print "simplification:", simplification
                return Variable(simplification)
        
        return self
    
    def replace(self, old, new):
        '''goes through this operator, replacing all instances of 'old' with 'new
        returns a new operator with the changes implemented
        '''
        pass
      
class Relation():
    '''the purpose of relations is to link different expressions, and for simplification'''
    def __init__(self, my_str1='', my_str2='', operator1=None, operator2=None):
        self.operator1 = operator1
        self.operator2 = operator2
        self.str1 = my_str1
        self.str2 = my_str2
    
    def break_down_side(self, rel_operator, exp_operator, _depth=0):
        '''Part of constructing an equivalent expression in a relation.
        By default, the LHS is broken down. This function is performed
        recursively, and kept track by means of the _depth variable
        '''
        # walk through the children belonging to both the representation and the expression
        # comparing them one by one. When a variable is found in the representation,
        # then save it in the rep_dict as the key, and the expression as the value.
        rel_dict = {} # a dictionary that keeps track of the variables in the relation
        #print "rel_operator.name:", rel_operator.name
        #print "exp_operator.name:", exp_operator.name
        if isinstance(rel_operator, Variable): # only adding a leaf expression to the dictionary
            #print "found leaf:", rel_operator.name
            rel_dict[rel_operator.name] = exp_operator
        else: # then its an Operator
            for i in range(len(rel_operator.children)): # loop thru the children
                rel_child = rel_operator.children[i]
                exp_child = exp_operator.children[i]
                child_rel_dict = self.break_down_side(rel_child, exp_child, _depth=_depth+1) # calling them recursively
                rel_dict.update(child_rel_dict) # combine the dictionary found in the recursion
                
        return rel_dict     
        
    def build_up_side(self, rel_expression, rel_dict):
        '''The second half of the construction of an equivalent expression in a
        relation. By default, the RHS of the relation is built back up.
        '''
        #print "rel_dict:", rel_dict #, "rel_expression:", rel_expression.collapse()
        assert rel_expression, "None expression caught"
        
        if isinstance(rel_expression, Variable):
            #print "Variable found:", rel_expression.name
            if rel_expression.name in rel_dict.keys(): # if this variable is in the dictionary
                #print "building up:", rel_dict[rel_expression.name]
                return rel_dict[rel_expression.name] # then return this expression
            else: # then it wasn't found in the dictionary
                return rel_expression # then just return whatever was in this relation
        else: # then it's an operator, we will need to call children recursively
            new_children = []
            new_operation = rel_expression.operator
            for i in range(len(rel_expression.children)): # loop thru the children
                #print "Operator my_expression:", rel_expression.name
                rel_child = rel_expression.children[i]
                new_child = self.build_up_side(rel_child, rel_dict) #recursive call on child
                new_children.append(new_child)
            new_expr = Operator(new_operation, new_children) # create a new expression with the proper variables in place
            #print "building up:", new_expr.collapse()
        return new_expr
    
    def construct(self, src_expr, src_side=1):
        '''given that an operator matches this relation, will return the resulting operator as predicted by the match'''
        assert src_side in [1,2], "The 'side' variable must be 1 or 2. Value not allowed: {side}".format(side=src_side)
        if src_side == 1: # breaking down the LHS
            breakdown_operator = self.operator1
            buildup_operator = self.operator2
        elif src_side == 2: # breaking down the RHS
            breakdown_operator = self.operator2
            buildup_operator = self.operator1
        dest_side = (src_side%2)+1 # get opposite of 1 or 2
        rep_dict = self.break_down_side(breakdown_operator, src_expr)
        new_expr = self.build_up_side(buildup_operator, rep_dict)
        return new_expr
    
    def compare(self, operator, my_operator=None, both_ways=False):
        '''compare myself to some expression (operation) to see whether we are comparable'''
        compares = None
        if my_operator==None: # then nobody provided anything
            my_operator = self.operator1
        if isinstance(operator, Variable):
            if isinstance(my_operator, Variable): # if they are both variables
                if is_numeric(my_operator.name): # if the relation is a numerical value
                    if operator.name == my_operator.name: # they must have the same numerical value
                        return operator
                        #return self.construct(operator) # they match, so return the operator itself
                    #else:
                    #    return False
                elif is_alphabet(my_operator.name): # the relation is an alphabetic value
                    return operator
                    #return self.construct(operator) # they match, so return the operator
            #elif isinstance(self.operator1, Operator): # THIS WILL NEVER MATCH
            #    return False
                
        elif isinstance(operator, Operator):
            if isinstance(my_operator, Variable): # an operator matching a relation variable
                if is_alphabet(my_operator.name): # the relation is an alphabetic value
                    return self.construct(operator) # then the operator matches the relation
                    
            elif isinstance(my_operator, Operator):
                if my_operator.name == operator.name: # then the relation has the same operation
                    # now see if the children match the provided pattern
                    if len(my_operator.children) == len(operator.children): # make sure we have the same number of children
                        #children_match = [] # a list of matching children
                        brokeout = False
                        for index in range(len(my_operator.children)):
                            op_child = operator.children[index] # operator child
                            rel_child = my_operator.children[index] # relation child
                            this_child = self.compare(op_child, rel_child)# then submit recursively
                            if not this_child: # if the child is still not matched
                                brokeout = True
                                break
                        if brokeout == False:
                            return self.construct(operator) # if we made it through the children, then the match is True
                      
        if both_ways == True: # then compare the relation backwards as well # TODO: fill this out eventually
            if self.operator2 == operator.name: # then the relation has the same operation
            # now see if the children match the provided pattern
                pass
        
        return compares

def op2rel(op):
    '''converts a Operator object to a Relation object.'''
    #new_str = op.str
    print "OP2REL ENTERED"
    rel = Relation(my_str1='', operator1=op)
    return rel

def is_alphabet(str):
    '''returns whether a string is alphabetic (numbers allowed after first character)'''
    if re.match('[a-zA-Z_]\w*',str):
        return True
    else:
        return False
  
def is_numeric(str):
    '''returns whether a string is numeric'''
    if re.match('[0-9]+',str):
        return True
    else:
        return False

def make_operator(mystr, spots, pos_spot, neg_spot=None):
    '''given a string and the positions of operators, returns an operator object'''
    old_spot = 0
    expr_list = []
    for spot in spots:
        if spot > 0: # then it's an add
            new_spot = spot
            operator = pos_spot
        elif spot < 0: # then it's a subtract
            new_spot = -spot
            operator = neg_spot
        branch = mystr[old_spot:new_spot]
        sub_expr = str_to_expr(branch)
        expr_list.append(sub_expr)
        #expr_list.append(operator) # Operator?
        old_spot = new_spot + 1
    branch = mystr[old_spot:]
    sub_expr = str_to_expr(branch)
    expr_list.append(sub_expr)
    return Operator(operator, expr_list)

def make_all_relations(relations):
    '''returns a list of rel objects'''
    assert len(relations) % 2 == 0, 'There must be an odd number of relations.'
    num_rels = len(relations) / 2
    rel_list = []
    for i in range(num_rels): 
        str1 = relations[i*2]
        str2 = relations[i*2+1]
        print "str1:", str1, "str2:", str2
        rel = make_relation(str1, str2)
        rel_list.append(rel)
    return rel_list

def make_relation(my_str1, my_str2):  
    '''given a pair of relation strings, will create an object for the relation for easy pattern matching'''
    expr1 = str_to_expr(my_str1)
    expr2 = str_to_expr(my_str2)
    new_rel = Relation(my_str1=my_str1, my_str2=my_str2, operator1=expr1, operator2=expr2, )
    return new_rel

def str_to_expr(mystr):
        '''given a string, will parse into a tree of expressions, variables
           and operators.'''
        depth = 0
        branch = '' # a branching out expression
        index = 0
        branch_start_index = 0
        
        add_sub_spots = []
        mult_div_spots = []
        power_spots = []
        mystr = mystr.strip()
        for char in mystr: # TODO: Add parenthesis support
            if char == '(': # opening a branch
                depth += 1 # traversing deeper into the tree
                if depth == 1: # get this branch ready for traversal recursively
                    branch_start_index = index + 1 # the next character starts the branch
            elif char == ')': # closing a branch
                depth -= 1 # returning back up it
                if depth == 0: # then we've closed off the shallowest branch
                    #branch = mystr[branch_start_index:index]
                    #print "recursing new branch:", branch
                    
                    pass
            if depth == 0:
                if char == '+': # then we've hit an add operator
                    add_sub_spots.append(index)
                    #branch = mystr[branch_start_index, index]
                    
                    #branch_start_index = index + 1
                elif char == '-':
                    add_sub_spots.append(-index)
                elif char == '*':
                    mult_div_spots.append(index)
                elif char == '/':
                    mult_div_spots.append(-index)
                elif char == '^':
                    power_spots.append(index)
                    
            index += 1

        if add_sub_spots:
            my_operator = make_operator(mystr, add_sub_spots, '+', '-')
            return my_operator
        
        if mult_div_spots:
            my_operator = make_operator(mystr, mult_div_spots, '*', '/')
            return my_operator

        if power_spots:
            my_operator = make_operator(mystr, power_spots, '^')
            return my_operator

        return Variable(mystr)
             

def deriv(expr, x):
    '''Given a function 'func', will compute the first derivative
      with respect to x.'''
    
    if isinstance(expr, Variable): # base case
        new_var = Variable()
        #print "found variable:", expr.name
        if expr.name == x: # if this is the variable
            new_var.name = "1" # the base case
        else:
            new_var.name = "0"
        return new_var

    elif isinstance(expr, Operator):
        new_op = Operator()
        if expr.name in ['+','-']: # add or subtract
            #print "found addition"
            new_op.name = expr.name # same operation
            for child in expr.children: # loop thru the children
                #print "descending down the tree after the next branch (addition)"
                new_child = deriv(child, x) # get the derivatives of the children recursively
                #print "new_child:", new_child.collapse()
                #print "adding child to addition operator"
                new_op.children.append(new_child)
            
        if expr.name == '*':
            #print "found multiplication"
            new_op.name = '+'
            new_child1 = Operator('*', [deriv(expr.children[0], x), expr.children[1]])
            #print "new_child1:", new_child1.collapse()
            #print "adding child to multiplication operator"
            new_op.children.append(new_child1)
            side1 = expr.children[0]
            #print "side1:", side1.collapse()
            #print "expr.children[1].collapse():", expr.children[1].collapse()
            side2 = deriv(expr.children[1], x)
            #print "side2:", side2.collapse()
            new_child2 = Operator('*', [side1, side2])
            #print "new_child2:", new_child2.collapse()
            #print "adding child to multiplication operator"
            new_op.children.append(new_child2)
            
        if expr.name == '^':
            #print "found power"
            new_op.name = '*'
            #new_child1 = expr.children[1]
            new_child1 = Operator('*', [expr.children[1], deriv(expr.children[0], x)])
            #print "new_child1:", new_child1.collapse()
            new_op.children.append(new_child1)
            new_child2 = Operator('^', [expr.children[0], Operator('-', [expr.children[1],Variable('1')])])
            #print "new_child2:", new_child2.collapse()
            new_op.children.append(new_child2)
            #new_child3 = deriv(expr.children[0], x)
            #print "new_child3:", new_child3.collapse()
            #new_op.children.append(new_child3)
            
        return new_op
    '''
    m = re.match('^%s$' % x, func)
    if m:
        return "1"
    
    m = re.match('%s\*\*(\d*\.?\d+)$' % x, func) # if there's a simple exponent expression
    if m:
        n = float(m.group(1)) # the value of the exponent
        n_minus_1 = eval("%d-1" % n)
        return '%d * %s**%d' % (n, x, n_minus_1)
    
    #if not re.search('+',func): # there are no additions in this function
        

    # split by additions
    sum_list = re.split('+', func)
    for element in sub_list:
        sub_deriv = deriv(element, x)
    deriv = " + ".join(sub_deriv)
    '''
    return deriv

#print "deriv(test_func)"
#print deriv(test_func, 'x')

simpl = make_all_relations(simplifications)

test_func = "(2 + x*y^3) + x^2"
print "test_func:", test_func
func = str_to_expr(test_func)
print "func (reprint):", func.collapse()
d = deriv(func,'y')
print "d:", d.collapse()
d = d.simplify(simpl)
print "d simplified:", d.collapse()
#rel = make_relation('a+0', 'a')
#print "rel.compare(d):", rel.compare(d).collapse()

'''
dumb1 = 'x + x + 0'
print "dumb1:", dumb1
rel = make_relation('a+0', '0')
dumb1 = str_to_expr(dumb1)
print "len(d.children):", len(d.children)
print "rel.compare(d):", rel.compare(d)
'''

