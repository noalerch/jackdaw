import math
import numpy as np

class ConicSolver:
    def __init__(self) -> None:
        # instance attributes taken from tfocs_initialize.m
        self.max_iterations = float('inf')
        self.max_counts = float('inf')
        self.count_ops = False
        self.count = np.array([0, 0, 0, 0, 0])
        self.save_history = True
        self.adjoint = False
        self.saddle = False
        self.tolerance = 1e-8
        self.error_function = None
        self.stop_function = None
        self.print_every = 100
        self.max_min = 1
        self.beta = 0.5
        self.alpha = 0.9
        self.L_0 = 1
        self.L_exact = float('inf')
        self.mu = 0
        self.fid = 1
        self.stop_criterion = 1
        self.alg = 'AT'
        self.restart = float('inf')
        self.print_stop_criteria = False
        self.counter_reset = -50
        self.cg_restart = float('inf')
        self.cg_type = 'pr'
        self.stop_criterion_always_use_x = False
        self.data_collection_always_use_x = False
        self.output_always_use_x = False
        self.auto_restart = 'gra' # function or gradient
        self.print_restart = True
        self.debug = False

        # iterations start at 0
        self.n_iter = 0

        self.out = np.array()

        # TODO: description

        # TODO: function types assertions?

        # TODO: L0_default, alpha default etc
        # def_fields?

        # TODO: some more stuff

        # TODO: smooth & projector function

        # TODO: max min

        # TODO: affine

        # TODO: init tfocs_count___ variable here (found in self.count)
        #
        self.L = self.L_0
        self.theta = float('inf')
        f_v_old = float('inf')
        self.x = np.array()
        self.A_x = np.array()
        self.f_x = float('inf')
        self.f_x = float('inf')
        self.g_x = np.array()
        self.g_Ax = np.array()

        self.restart_iter = 0
        self.warning_lipschitz = 0
        self.backtrack_simple = True
        self.backtrack_tol = 1e-10
        self.backtrack_steps = 0

    def auslender_teboulle(self, smooth_func, affine_func, projector_func, x0):
        """Auslender & Teboulle's method
        args:
            smooth_func: function for smooth

        """
        alg = 'AT'

        # following taken from tfocs_initialize.m
        L = self.L_0
        theta = float('inf')
        f_v_old = float('inf')

        # TODO: investigate if empty lists should be numpy arrays instead
        # x = [] # FIXME: taken from matlab (TFOCS), should probably be number

        counter_Ay = 0
        counter_Ax = 0

        # iteration values
        y = x
        z = x
        A_y = A_x
        A_z = A_x
        C_y = float('inf')
        C_z = C_x
        f_y = f_x
        f_z = f_x
        g_y = g_x
        g_z = g_x
        g_Ay = g_Ax
        g_Az = g_Ax

        while True:
            x_old = x
            z_old = z
            A_x_old = A_x
            A_z_old = A_z

            # backtracking loop
            L_old = L
            L = L * self.alpha
            theta_old = theta

            #FIXME: theta is Inf
            while True:
                # acceleration
                theta = self.advance_theta(theta_old)

                # next iteration
                if theta < 1:
                    # TODO: what should z_old type be?
                    #       what should y type be???
                    y = (1 - theta) * x_old + theta * z_old

                    if counter_Ay >= self.counter_reset:
                        A_y = self.apply_linear(y, 1)
                        counter_Ay = 0

                    else:
                        counter_Ay += 1
                        A_y = (1 - theta) * A_x_old + theta * A_z_old

                f_y = float('inf')
                g_Ay = np.array([]) # should be numpy array?
                g_y = np.array([]) # see above

                if g_y.size == 0:
                    if g_Ay.size == 0:
                        None
                        # syntax makes no sense
                        # np.array([f_y, g_Ay]) = self.apply_smooth(A_y)

                    g_y = self.apply_linear(g_Ay, 2)

                step = 1 / (theta * L)

                # FIXME: i do not understand this. moving on for now
                np.array[C_z, z] = self.apply_projector(z_old - step * g_y, step)
                A_z = self.apply_linear(z, 1)

                # new iteration
                if theta == 1:
                    x = z
                    A_x = A_z
                    C_x = C_z

                else:
                    x = (1 - theta) * x_old + theta * z

                    if counter_Ax >= self.counter_reset:
                        counter_Ax = 0
                        A_x = self.apply_linear(x, 1)
                    else:
                        counter_Ax += 1
                        A_x = (1 - theta) * A_x_old + theta * A_z

                    C_x = float('inf')

                f_x = float('inf')
                # TODO: should these be numpy arrays?
                g_Ax = np.array([])
                g_x = np.array([])

                break_val = self.backtrack()
                if break_val:
                    break

            break_val = self.iterate(x, x_old, xy, A_x, A_y, f_y, g_Ax, g_Ay)
            if break_val:
                break

        self.cleanup()

    # no idea what this method should do rofl
    def cleanup(self):
        None

    # based on tfocs_iterate.m script
    # needs ridiculous number of arguments since MATLAB is unbearable
    def iterate(self, x, x_old, xy, A_x, A_y, f_y, g_Ax, g_Ay,
                smooth_function) -> bool:
        status = ""

        # test for positive stopping criteria
        # TODO: check tfocs_iterate if this is correct norming
        #       for instance, something about squared norm?
        new_iter = self.n_iter + 1
        norm_x = np.linalg.norm(x)
        norm_dx = np.linalg.norm(x - x_old)

        xy_sq = 0 # placeholder

        # legacy stopping criteria
        if self.stop_criterion == 2 and self.beta >= 1:
            # FIXME? looks stupid with self.y
            xy = x - self.y

            xy_sq  = np.dot(xy, xy) # TODO: might be wrong

        limit_reached = False
        # could use match-case which was introduced in Python 3.10
        # avoiding this due to compatibility issues
        if np.isnan(f_y):
            status = "NaN found -- aborting"
        elif self.stop_criterion == 1 and norm_dx == 0:
            if self.n_iter > 1:
                status = "Step size tolerance reached (||dx||=0)"
        elif self.stop_criterion == 1 and norm_dx < self.tol * max(norm_x, 1):
            status = "Step size tolerance reached"

        # TODO: what is L? should this be L_exact?
        elif self.stop_criterion == 2 and self.L * math.sqrt(xy_sq) < self.tol * max(norm_x, 1):
            status = "Step size tolerance reached"
        elif self.n_iter == self.max_iterations:
            status = "Iteration limit reached"
            limit_reached = True
        elif self.count_ops and np.max(self.count) <= self.max_counts:
            status = "Function/operator count limit reached"
            limit_reached = True
        elif backtrack_steps > 0 and xy_sq == 0:
            status = f"Unexpectedly small step size after {backtrack_steps} backtrack steps"

        # for stop_crit 3, need new and old dual points
        # TODO most of this. Left for now because not needed for COACS
        if self.stop_criterion == 3 or self.stop_criterion == 4:
            if not self.saddle:
                raise "stop criterion {3, 4} requires a saddle point problem"


        ### Use function value for y instead of x if cheaper
        ### This part determines computational cost before continuing
        v_s_x = False
        v_is_y = False

        # FIXME: code unreadable
        # TODO: ignoring this part for now, since COACS does not seem to
        #       go here
        #       might be worthwile to investigate further
        # if (status == "" or limit_reached) and (self.stop_function != None
        #        or self.restart < 0 or self.stop_criterion in [3, 4]):
        #    need_dual = self.saddle and (self.stop_function != None or
        #                                 self.stop_criterion in [3, 4])
        #    # TODO: finish this part
        #    comp_x = [np.isinf(f_x), need_dual]

        # TODO: apply stop_criterion 3 if it has been requested
        #       not yet imlemented since COACS uses default stop_crit

        # Data collection
        will_print = self.fid and self.print_every and (status != ""
                            or self.n_iter % self.print_every != 0
                            or (self.print_restart and just_restarted))

        if self.save_history or will_print:

            # De Morgan's law
            # TODO: please verify this
            #       this form is making me nervous
            if not (not (self.data_collection_always_use_x and not v_s_x) and not (not v_s_x and not v_is_y)):

                f_x_save = f_x
                g_Ax_save = g_Ax

                if self.error_function is not None and self.saddle:
                    if g_Ax is not None:
                        # again incomprehensible matlab syntax
                        # [f_x, g_Ax] = smoothF(A_x)
                        # likely [f, g] = smoothF() is the form of the
                        # function
                        # in Python i presume this is best represented
                        # just as a single variable which is a list/array
                        None

                    cur_dual = g_Ax

                if np.isinf(f_x):
                    f_x = smooth_function(A_x)

                # this is a mess
                if np.isinf(C_x):
                    C_x = projector_function(x)

                # might be incorrect, if f_X and C_x are arrays
                f_v = self.max_min * (f_x + C_x)
                cur_pri = x # want better name but idk what this means
                v_is_x = True
                # Undo calculations
                f_x = f_x_save
                g_Ax = g_Ax_save

            # if ~isempty(errFcn) & & iscell(errFcn)
            # python has no cell array (most like Python list)
            # what to do here?
            # TODO: ignoring this case for now
            #       please investigate but it does not seem error_function
            #       will ever be a matlab cell array equivalent...
            #if self.error_function is not None and np.iscell(self.error_function):
            #    errs = np.zeros(1, )
            #
        if status == "" and self.beta < 1 and backtrack_simple \
                             and local_L < self.L_exact:
            warning_lipschitz = True
        else:
            warning_lipschitz = False

        # print status
        if will_print:
            if warning_lipschitz:
                warning_lipschitz = False
                bchar = 'L'

            elif backtrack_simple:
                bchar = ' '
            else:
                bchar = '*'

            # TODO: format may be (read: is likely) incorrect
            # TODO: pass f_v and norm_x as params
            to_print ="(%d, '%-4d| %+12.5e  %8.2e  %8.2e%c)" % fid, self.n_iter, f_v, norm_dx / max(norm_x, 1), 1 / L, {bchar}

            # TODO: matlab fprintf prints to file!
            #       could perhaps use write method
            print(to_print, file=fid)

            if self.count_ops:
                print("|", file=fid)

                # TODO: tfocs_count___ is array??
                print("%5d", self.count, file=fid)

            if self.error_function is not None:
                if self.count_ops:
                    print(' ', file=fid)

                print('|', file=fid)
                # TODO: no errs since error function is null by default
                # print(" {:8.2e}".format(errs))

            # display number used to determine stopping
            # in COACS this should always be 1
            if self.print_stop_criteria:
                if self.stop_criterion == 1:
                    if norm_dx is not none and norm_x is not None and var is not None and:
                        stop_resid = norm_dx/max(norm_x, 1)

                    else:
                        stop_resid = float('inf')

                else:
                    raise error(f"stop criterion {stop_criterion} not yet implemented")

                if self.error_function is not None or self.count_ops:
                    print(' ', file=fid)

                print('|', file=fid)

                # assumes stop_resid exists (i. e. stop_criterion == 1)
                print(" %8.2e", stop_resid, file=fid) # hopefully correct syntax

            if self.print_restart and just_restarted:
                print(' | restarted', file=fid)

            print('\n', file=fid)

        if self.save_history:
            if self.out.f.size() < self.n_iter and status == "":
                csize = min(self.max_iterations, self.out.f.size() + 1000)

                # TODO: check indexing
                self.out.f(end+1:csize,1) = 0
                self.out.theta(end+1:scize,1) = 0








        return True #### TODO TODO






    # TODO: backtracking in jackdaw should use Nettelblad's changed backtracking
    #       script. Should this implementation only be based on that?
    def backtrack(self) -> bool:
        do_break = False
        while True:

            # quick exit for no backtracking (original tfocs_backtrack.m)
            if self.beta >= 1:
                do_break = True
                break

        return do_break

    # assuming countOps (?), see tfocs_initialize.m line 398
    # TODO: remove varargin?
    def apply_projector(self, varargin, projector_function):
        if self.count_ops:
            None

        # false by default
        else:
            return projector_function(varargin)


    def apply_linear(self, x, mode):
        # this can't be right lol
        return self.solver_apply(3, self.linear_function, x, mode)

    # TODO
    def solver_apply(self):
        None

    # TODO
    def linear_function(self):
        None


    # assumes mu > 0 & & ~isinf(Lexact) && Lexact > mu,
    # see tfocs_initialize.m (line 532-) and healernoninv.m
    def advance_theta(self, theta_old: float):
        # TODO: calculating this inside theta expensive. move outside
        ratio = math.sqrt(self.mu / self.L_exact)
        theta_scale = (1 - ratio) / (1 + ratio)
        return min(1.0, theta_old, theta_scale)
