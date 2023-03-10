"""Sewing Training-Based Optimization."""

import tensorflow as tf
import metaopts.utilities as mou


def stbo(
        model_weights,
        model_fitness_fn,
        generation_limit,
        fitness_limit,
        population_size,
        transfer_learning=False,
        fitness_log_frequency=-1,
        best_individual_save_frequency=-1,
        lb=-1.0,
        ub=1.0
    ):
    """
    Implementation of the Sewing Training-Based Optimization algorithm.

    Args:
        model_weights: `list` of `tf.Variable` - List of model weights.
        model_fitness_fn: `tf.function` - Fitness function generated by `metaopts.create_fitness`.
        generation_limit: `int` - Maximum number of generations.
        fitness_limit: `float` - Fitness value threshold.
        population_size: `int` - Number of individuals in the population.
        transfer_learning: `bool` - Whether to use transfer learning.
        fitness_log_frequency: `int` - Frequency of logging fitness values to the log file. If set to -1, no logging is performed.
        best_individual_save_frequency: `int` - Frequency of saving the best individual to a pickle file. If set to -1, no saving is performed.
        lb: `float` - Lower bound of the search space.
        ub: `float` - Upper bound of the search space.
    
    Notes:

    * The source code is based on the pseudocode and the equations provided in the paper.

    Reference:

    * Dehghani, Mohammad & Trojovska, Eva & Zuščák, Tomáš. (2022).
    A new human-inspired metaheuristic algorithm for solving optimization problems based on mimicking sewing training.
    Scientific Reports. 12. 10.1038/s41598-022-22458-9.
    """

    def eq_2():
        if transfer_learning:
            return mou.create_population(model_weights, N, True)
        return [tf.Variable(lb + tf.random.uniform((N,) + weights.shape, 0, 1)*(ub-lb)) for weights in model_weights]

    def eq_3():
        return tf.Variable(tf.zeros(N, dtype=tf.float32))

    @tf.function
    def eq_4(index):
        mou.print_function_trace('eq_4')
        CSI = tf.cast(tf.reshape(tf.where(F < F[index]), (-1,)), dtype=tf.int32)
        if tf.equal(tf.size(CSI), 0):
            return tf.expand_dims(index, 0)
        return CSI
    
    @tf.function
    def eq_5():
        mou.print_function_trace('eq_5')
        for x, xp in zip(X, XP):
            shape = tf.shape(x)
            r = tf.random.uniform(shape, 0, 1, dtype=tf.float32)
            I = tf.cast(tf.random.uniform(shape, 1, 3, dtype=tf.int32), dtype=tf.float32)
            xp.assign(x + r*(tf.gather(x, SI) - I*x))

    @tf.function
    def eq_7_and_8():
        mou.print_function_trace('eq_7_and_8')
        for x, xp in zip(X, XP):
            shape = tf.shape(x)
            m = tf.cast(tf.size(x), dtype=tf.float32)
            ms = tf.cast(tf.round(1 + gen/(2*T)*m), dtype=tf.int32)
            SDi = tf.random.shuffle(tf.range(m, dtype=tf.int32))[:ms]
            x_flat = tf.reshape(x, (-1,))
            instructors_flat = tf.reshape(tf.gather(x, SI), (-1,))
            xp_flat = tf.tensor_scatter_nd_update(x_flat, tf.expand_dims(SDi, 1), tf.gather(instructors_flat, SDi))
            xp.assign(tf.reshape(xp_flat, shape))
    
    @tf.function
    def eq_10():
        mou.print_function_trace('eq_10')
        for x, xp in zip(X, XP):
            r = tf.random.uniform(x.shape, 0, 1, dtype=tf.float32)
            xp.assign(tf.clip_by_value(x + (lb + r*(ub-lb))/gen, lb, ub))

    @tf.function
    def update_improved_positions():
        mou.print_function_trace('update_improved_positions')
        mou.update_population_fitness(model_weights, model_fitness_fn, F, X, N)
        mou.update_population_fitness(model_weights, model_fitness_fn, FP, XP, N)
        improved_positions = FP < F
        for x, xp in zip(X, XP):
            F_shape = tf.concat([[N], tf.ones(tf.rank(x) - 1, dtype=tf.int32)], axis=0)
            x.assign(tf.where(tf.reshape(improved_positions, F_shape), xp, x))
        F.assign(tf.where(improved_positions, FP, F))

    @tf.function
    def update_SI():
        mou.print_function_trace('update_SI')
        for i in tf.range(N):
            CSI = eq_4(i)
            candidate_count = tf.size(CSI)
            selected_instructor = tf.random.uniform((), 0, candidate_count, dtype=tf.int32)
            SI[i].assign(CSI[selected_instructor])

    # Adjust N and T
    N = tf.constant(population_size, dtype=tf.int32)
    T = tf.constant(generation_limit, dtype=tf.float32)

    # Initialize the STBO population by (2) and create vector F of the values of the objective function by (3)
    X = eq_2()
    F = eq_3()
    mou.update_population_fitness(
        model_weights=model_weights,
        model_fitness_fn=model_fitness_fn,
        fitness_values=F,
        population=X,
        population_size=N
    )

    # Initialize other pseudo-code variables
    lb = tf.constant(lb, dtype=tf.float32)
    ub = tf.constant(ub, dtype=tf.float32)
    SI = tf.Variable(tf.zeros(N, dtype=tf.int32))
    XP = [tf.Variable(x) for x in X]
    FP = tf.Variable(F)
    best_fitness = tf.Variable(tf.reduce_min(F), dtype=tf.float32)
    gen = tf.Variable(0.0, dtype=tf.float32)

    # Print debug information
    algo_name = 'Sewing Training-Based Optimization'
    mou.print_algo_start(algo_name)

    # For t = 1 to T
    while best_fitness > fitness_limit and gen <= T:
        
        # Phase 1: Training (exploration)
        # Determine the set of candidate training instructors for the ith member by (4)
        # Choose the training instructor SI from CSI to teach sewing the ith STBO member
        update_SI()

        # Calculate the new position for the ith STBO member using (5)
        eq_5()

        # Update the position of the ith STBO member using (6)
        update_improved_positions()

        # Phase 2: Imitation of the instructor skills (exploitation)
        # Calculate SD using Equation (7)
        # Calculate the new position of the ith STBO member using Equation (8)
        eq_7_and_8()

        # Update the position of the ith STBO member using (9)
        update_improved_positions()

        # Phase 3: Practice (exploitation)
        # Calculate the new position for the ith STBO member using (10)
        eq_10()

        # Update the position of the ith STBO member using (11)
        update_improved_positions()

        # Update the best candidate solution
        best_fitness.assign(tf.reduce_min(F))

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
                population=X,
                individual_index=tf.argmin(F),
                file_path='{0} weights'.format(algo_name)
            )

        # Print training information
        mou.print_training_status(
            generation=int(gen),
            generation_limit=int(T),
            best_fitness_value=float(best_fitness)
        )

        gen.assign_add(1)


    # Print debug information
    mou.print_algo_end(algo_name)

    # Apply best solution to the model
    mou.apply_best_solution(
        model_weights=model_weights,
        model_fitness_fn=model_fitness_fn,
        fitness_values=F,
        population=X,
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
            population=X,
            individual_index=tf.argmin(F),
            file_path='{0} weights'.format(algo_name)
        )
