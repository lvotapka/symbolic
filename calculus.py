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

'''

import math, re
from copy import deepcopy

simplifications = [
'x + 0', 'x',
'x * 1', 'x',
'x^1', 'x',
]

# idea: expression classes that point to further expression classes
class Expression():
    def __init__(self, expr=[]):
        self.expr = expr # a list of variables and operators and other expressions
        self.str = ''

    def __str__(self):
        return self.expr
        
class Variable(): # leaves on the tree
    def __init__(self, value=None):
        self.name = value

    def __str__(self):
        return self.name

    def collapse(self):
        '''return a string representation of myself'''
        return self.name

class Operator(): # forks in the tree
    def __init__(self, operator=None, children=[]):
        self.name = operator
        self.children = children

    def __getitem__(self, key):
        return self.children[key]

    def __str__(self):
        return self.name

    def collapse(self):
        '''Reduce this operator to a string representation of itself'''
        collapsed_children = [] # creepy name
        print "collapsing operator:", self.name
        for child in self.children:
            print "collapsing child:", child.name
            collapsed_children.append(child.collapse())
        return self.name.join(collapsed_children)



test_func = "x^2 + x*y^3 + 2"

def make_operator(mystr, spots, pos_spot, neg_spot=None):
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
        for char in mystr: # TODO: I know how to make it only go through relevant pieces
            if char == '(': # opening a branch
                depth += 1 # traversing deeper into the tree
                if depth == 1: # get this branch ready for traversal recursively
                    branch_start_index = index + 1 # the next character starts the branch
            elif char == ')': # closing a branch
                depth -= 1 # returning back up it
                if depth == 0: # then we've closed off the shallowest branch
                    #branch = mystr[branch_start_index:index]
                    print "recursing new branch:", branch
                    #sub_expr = Expression(str_to_expr(branch))
            if depth == 0:
                if char == '+': # then we've hit an add operator
                    add_sub_spots.append(index)
                    #branch = mystr[branch_start_index, index]
                    #sub_expr = Expression(str_to_expr(branch))
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
        
            

 
def compare(expr, relation): # searches up the expression tree to see whether the relation matches it
    pass
        

def deriv(expr, x):
    '''Given a function 'func', will compute the first derivative
      with respect to x.'''
    
    if isinstance(expr, Variable): # base case
        new_var = Variable()
        print "found variable:", expr.name
        if expr.name == x: # if this is the variable
            new_var.name = "1" # the base case
        else:
            new_var.name = "0"
        return new_var

    elif isinstance(expr, Operator):
        new_op = Operator()
        if expr.name in ['+','-']: # add or subtract
            print "found addition"
            new_op.name = expr.name # same operation
            for child in expr.children: # loop thru the children
                print "descending down the tree after the next branch (addition)"
                new_child = deriv(child, x) # get the derivatives of the children recursively
                print "new_child:", new_child.collapse()
                print "adding child to addition operator"
                new_op.children.append(new_child)
            
        if expr.name == '*':
            print "found multiplication"
            new_op.name = '+'
            new_child1 = Operator('*', [deriv(expr.children[0], x), expr.children[1]])
            print "new_child1:", new_child1.collapse()
            print "adding child to multiplication operator"
            new_op.children.append(new_child1)
            side1 = expr.children[0]
            print "side1:", side1.collapse()
            print "expr.children[1].collapse():", expr.children[1].collapse()
            side2 = deriv(expr.children[1], x)
            print "side2:", side2.collapse()
            new_child2 = Operator('*', [side1, side2])
            print "new_child2:", new_child2.collapse()
            print "adding child to multiplication operator"
            new_op.children.append(new_child2)
            
        if expr.name == '^':
            print "found power"
            new_op.name = '*'
            new_child1 = expr.children[1]
            print "new_child1:", new_child1.collapse()
            new_op.children.append(new_child1)
            new_child2 = Operator('^', [expr.children[0], Operator('-', [expr.children[1],Variable('1')])])
            print "new_child2:", new_child2.collapse()
            new_op.children.append(new_child2)
            new_child3 = deriv(expr.children[0], x)
            print "new_child3:", new_child3.collapse()
            new_op.children.append(new_child3)
            
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

print "test_func:", test_func
print "str_to_expr(test_func):"
x = str_to_expr(test_func)
d = deriv(x,'x')
print "x:", x.collapse()

