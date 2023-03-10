"""African Vultures Optimization Algorithm."""

import tensorflow as tf
import metaopts.utilities as mou
import math
from copy import deepcopy


def avoa(
        model_weights,
        model_fitness_fn,
        generation_limit,
        fitness_limit,
        population_size,
        transfer_learning=False,
        fitness_log_frequency=-1,
        best_individual_save_frequency=-1,
        L1=0.8,
        L2=0.2,
        w=2.5,
        P1=0.6,
        P2=0.4,
        P3=0.6,
        lb=-1,
        ub=1,
        beta=1.5
    ):
    """
    Implementation of the African Vultures Optimization Algorithm.

    Args:
        model_weights: `list` of `tf.Variable` - List of model weights.
        model_fitness_fn: `tf.function` - Fitness function generated by `metaopts.create_fitness`.
        generation_limit: `int` - Maximum number of generations.
        fitness_limit: `float` - Fitness value threshold.
        population_size: `int` - Number of vultures in the population.
        transfer_learning: `bool` - Whether to use transfer learning.
        fitness_log_frequency: `int` - Frequency of logging fitness values to the log file. If set to -1, no logging is performed.
        best_individual_save_frequency: `int` - Frequency of saving the best individual to a pickle file. If set to -1, no saving is performed.
        L1: `float` - Probability of choosing the best vulture.
        L2: `float` - Probability of choosing the second best vulture.
        w: `float` - Parameter w in in equation (3).
        P1: `float` - Probability P1.
        P2: `float` - Probability P2.
        P3: `float` - Probability P3.
        lb: `float` - Lower bound of the search space in equation (8).
        ub: `float` - Upper bound of the search space in equation (8).
        beta: `float` - Parameter of Levy flight.

    Notes:

    * The source code is based on the pseudocode and the equations provided in the paper.
        
    Reference:

    * Abdollahzadeh, Benyamin & Soleimanian Gharehchopogh, Farhad & Mirjalili, Seyedali. (2021).
    African Vultures Optimization Algorithm: A New Nature-Inspired Metaheuristic Algorithm for Global Optimization Problems.
    Computers & Industrial Engineering. early. 1.10.1016/j.cie.2021.107408.
    """

    @tf.function
    def update_best_vultures():
        mou.print_function_trace('update_best_vultures')
        best_indices = tf.argsort(fitness_values)[:2]
        for bv, p in zip(best_vultures, P):
            bv.assign(tf.gather(p, best_indices))

    @tf.function
    def eq_1():
        mou.print_function_trace('eq_1')
        reversed = tf.reduce_sum(L) / L
        logits = tf.math.log(reversed)
        selected = tf.random.categorical([logits], 1, dtype=tf.int32)
        for r, bv in zip(R, best_vultures):
            r.assign(bv[selected[0][0]])

    @tf.function
    def eq_3():
        mou.print_function_trace('eq_3')
        h = tf.random.uniform((), -2, 2)
        return h * (tf.pow(tf.sin(math.pi/2 * gen/T), w) + tf.cos(math.pi/2 * gen/T) - 1)

    @tf.function
    def eq_4():
        mou.print_function_trace('eq_4')
        rand_1 = tf.random.uniform((), 0, 1)
        z = tf.random.uniform((), -1, 1)
        t = eq_3()
        F.assign((2*rand_1 + 1) * z * (1 - gen/T) + t)

    @tf.function
    def eq_6():
        mou.print_function_trace('eq_6')
        eq_7()
        for p, r, d in zip(P, R, D):
            p[i].assign(r - d*F)

    @tf.function
    def eq_7():
        mou.print_function_trace('eq_7')
        X = 2 * tf.random.uniform((), 0, 1)
        for d, r, p in zip(D, R, P):
            d.assign(tf.abs(X*r - p[i]))
    
    @tf.function
    def eq_8():
        mou.print_function_trace('eq_8')
        rand_2 = tf.random.uniform((), 0, 1)
        rand_3 = tf.random.uniform((), 0, 1)
        for p, r in zip(P, R):
            p[i].assign(r - F + rand_2*((ub-lb)*rand_3 + lb))

    @tf.function
    def eq_10():
        mou.print_function_trace('eq_10')
        eq_7()
        rand_4 = tf.random.uniform((), 0, 1)
        for r, p, d in zip(R, P, D):
            dt = r - p[i] # eq_11
            p[i].assign(d*(F+rand_4) - dt)
    
    @tf.function
    def eq_12():
        mou.print_function_trace('eq_12')
        rand_5 = tf.random.uniform((), 0, 1)
        rand_6 = tf.random.uniform((), 0, 1)
        for s, r, p in zip(S, R, P):
            s[0].assign(r * ((rand_5*p[i]) / (2*math.pi)) * tf.cos(p[i]))
            s[1].assign(r * ((rand_6*p[i]) / (2*math.pi)) * tf.sin(p[i]))

    @tf.function
    def eq_13():
        mou.print_function_trace('eq_13')
        eq_12()
        for p, r, s in zip(P, R, S):
            p[i].assign(r - (s[0]+s[1]))

    @tf.function
    def eq_15():
        mou.print_function_trace('eq_15')
        for a, bv, p in zip(A, best_vultures, P):
            a[0].assign(bv[0] - ((bv[0]*p[i]) / (bv[0]-tf.pow(p[i], 2))) * F)
            a[1].assign(bv[1] - ((bv[1]*p[i]) / (bv[1]-tf.pow(p[i], 2))) * F)

    @tf.function
    def eq_16():
        mou.print_function_trace('eq_16')
        eq_15()
        for p, a in zip(P, A):
            p[i].assign((a[0]+a[1]) / 2)

    @tf.function
    def eq_17():
        mou.print_function_trace('eq_17')
        eq_18()
        for p, r, l in zip(P, R, Levy):
            dt = r - p[i] # eq_11
            p[i].assign(r - tf.abs(dt)*F*l)

    @tf.function
    def eq_18():
        mou.print_function_trace('eq_18')
        for l in Levy:
            u = tf.random.uniform(l.shape, 0, 1)
            v = tf.random.uniform(l.shape, 0, 1)
            l.assign(0.01 * ((u*sigma) / tf.pow(tf.abs(v), 1/beta)))
    
    def calculate_sigma():
        return pow((math.gamma(1+beta) * math.sin((math.pi*beta) / 2))
                   / (math.gamma(1 + 2*beta) * beta * 2 * ((beta-1) / 2)),
                   1/beta)


    # Inputs: The population size N and maximum number of iterations T
    N = tf.constant(population_size, dtype=tf.int32)
    T = tf.constant(generation_limit, dtype=tf.float32)

    # Initialize the random population Pi (i = 1, 2, ..., N)
    P = mou.create_population(
        model_weights=model_weights,
        population_size=N,
        transfer_learning=transfer_learning
    )
    fitness_values = tf.Variable(tf.zeros(N, dtype=tf.float32))

    # Initialize other pseudo-code variables
    L = tf.constant([L1, L2], dtype=tf.float32)
    w = tf.constant(w, dtype=tf.float32)
    P1 = tf.constant(P1, dtype=tf.float32)
    P2 = tf.constant(P2, dtype=tf.float32)
    P3 = tf.constant(P3, dtype=tf.float32)
    lb = tf.constant(lb, dtype=tf.float32)
    ub = tf.constant(ub, dtype=tf.float32)
    beta = tf.constant(beta, dtype=tf.float32)
    sigma = tf.constant(calculate_sigma(), dtype=tf.float32)

    best_vultures = [tf.Variable(tf.zeros((2,) + weights.shape, dtype=tf.float32)) for weights in model_weights]
    S = deepcopy(best_vultures)
    A = deepcopy(best_vultures)

    R = [tf.Variable(tf.zeros(weights.shape, dtype=tf.float32)) for weights in model_weights]
    D = deepcopy(R)
    Levy = deepcopy(R)

    F = tf.Variable(0.0, dtype=tf.float32)
    best_fitness = tf.Variable(0.0, dtype=tf.float32)
    gen = tf.Variable(0.0, dtype=tf.float32)
    i = tf.Variable(0, dtype=tf.int32)

    # Print debug information
    algo_name = 'African Vultures Optimization Algorithm'
    mou.print_algo_start(algo_name)

    # while (stopping condition is not met) do
    while gen <= T:

        # Calculate the fitness values of Vulture
        mou.update_population_fitness(
            model_weights=model_weights,
            model_fitness_fn=model_fitness_fn,
            fitness_values=fitness_values,
            population=P,
            population_size=N
        )

        # Set PBestVulture1 as the location of Vulture (First best location Best Vulture Category 1)
        # Set PBestVulture2 as the location of Vulture (Second best location Best Vulture Category 2)
        update_best_vultures()

        # Update best fitness
        best_fitness.assign(tf.reduce_min(fitness_values))

        # Log fitness
        if fitness_log_frequency > 0:
            mou.log_fitness_value(
                fitness_value=float(best_fitness),
                log_file_name='{0} fitness'.format(algo_name),
                max_cache_size=fitness_log_frequency
            )

        # Save best individual
        if best_individual_save_frequency > 0 and gen % best_individual_save_frequency == 0:
            mou.save_individual(
                population=P,
                individual_index=tf.argmin(fitness_values),
                file_path='{0} weights'.format(algo_name)
            )

        # Print training information
        mou.print_training_status(
            generation=int(gen),
            generation_limit=int(T),
            best_fitness_value=float(best_fitness)
        )

        # Additional stopping condition
        if best_fitness < fitness_limit:
            break

        # for (each Vulture (Pi)) do
        i.assign(0)
        while i < N:

            # Select R(i) using Eq. (1)
            eq_1()
            
            # Update the F using Eq. (4)
            eq_4()

            # if (|F| >= 1) then
            if tf.abs(F) >= 1:

                # if (P1 >= randP1 ) then
                if P1 >= tf.random.uniform((), 0, 1):

                    # Update the location Vulture using Eq. (6)
                    eq_6()

                else:

                    # Update the location Vulture using Eq. (8)
                    eq_8()
            
            # if (|F| < 1) then
            else:

                # if (|F| >= 0.5) then
                if tf.abs(F) >= 0.5:

                    # if (P2 >= randP2 ) then
                    if P2 >= tf.random.uniform((), 0, 1):

                        # Update the location Vulture using Eq. (10)
                        eq_10()
                    
                    else:

                        # Update the location Vulture using Eq. (13)
                        eq_13()

                else:

                    # if (P3 >= randP3 ) then
                    if P3 >= tf.random.uniform((), 0, 1):

                        # Update the location Vulture using Eq. (16)
                        eq_16()
                    
                    else:

                        # Update the location Vulture using Eq. (17)
                        eq_17()

            i.assign_add(1)

        gen.assign_add(1)


    # Print debug information
    mou.print_algo_end(algo_name)

    # Apply best solution to the model
    mou.apply_best_solution(
        model_weights=model_weights,
        model_fitness_fn=model_fitness_fn,
        fitness_values=fitness_values,
        population=P,
        population_size=N
    )

    # Log fitness
    if fitness_log_frequency > 0:
        mou.log_fitness_value(
            fitness_value=float(best_fitness),
            log_file_name='{0} fitness'.format(algo_name),
            max_cache_size=fitness_log_frequency,
            force_file_write=True
        )

    # Save best individual
    if best_individual_save_frequency > 0:
        mou.save_individual(
            population=P,
            individual_index=tf.argmin(fitness_values),
            file_path='{0} weights'.format(algo_name)
        )
