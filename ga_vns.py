import random
import copy
import time
from collections import defaultdict

class GAVNSSolver:
    def __init__(self, jobs, machines_data, calculate_duration_fn, pop_size=100, max_gen=100, tightness_factor=1.5):
        """
        Khởi tạo bộ giải GA-VNS cho bài toán Flexible Job Shop Scheduling.
        jobs: List các job cần lập lịch.
        machines_data: Dữ liệu về các máy từ master_data.
        calculate_duration_fn: Hàm tính toán thời gian gia công (machine_id, material_group, size_mm).
        pop_size: Kích thước quần thể.
        max_gen: Số thế hệ tối đa.
        tightness_factor: Hệ số để tính Due Date (dựa theo phương pháp TWK).
        """
        self.jobs = jobs
        self.machines_data = machines_data
        self.calculate_duration = calculate_duration_fn
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.tightness_factor = tightness_factor
        
        self.num_jobs = len(jobs)
        self.job_dict = {job['id']: job for job in jobs}
        
        self.machine_list = list(self.machines_data.keys())
        
        # Tiền xử lý các lựa chọn máy cho từng nguyên công của job
        self.job_ops = [] # Lưu danh sách dạng (job_idx, op_idx, job_id)
        self.job_due_dates = {}
        self.job_priority_weight = {}
        self.total_work_content = {}
        
        # Precompute processing times and eligible machines
        self.processing_times = {} # (job_id, op_idx) -> {machine_id: duration}
        
        for job_idx, job in enumerate(self.jobs):
            twk = 0
            job_id = job['id']
            is_complex = job.get('complexity', 0) > 0.1
            required_cap = "Cut_contour" if is_complex else "Cut_straight"
            
            # processing_times calculation
            num_ops = len(job.get('operations', []))
            for op_idx in range(num_ops):
                self.job_ops.append((job_idx, op_idx, job_id))
                
                # Retrieve the specific operation name for this step
                # if the operations are just integers (old format fallback), we use required_cap
                op_val = job['operations'][op_idx]
                if isinstance(op_val, str):
                    op_req_cap = op_val
                else:
                    op_req_cap = required_cap

                # Filter eligible machines per operation
                eligible_machines = []
                for m_id, m_data in self.machines_data.items():
                    if op_req_cap in m_data.get('capabilities', []):
                        eligible_machines.append(m_id)
                        
                if not eligible_machines:
                    eligible_machines = ["MANUAL_FALLBACK"]

                op_times = {}
                min_time = float('inf')
                for m_id in eligible_machines:
                    if m_id == "MANUAL_FALLBACK":
                        dur = 120
                    else:
                        dur = self.calculate_duration(m_id, job.get('material_group', 'C'), job.get('size_mm', 1000))
                    
                    if job.get('slow_mode'):
                        dur = int(dur * 1.5)
                        
                    op_times[m_id] = dur
                    if dur < min_time:
                        min_time = dur
                
                self.processing_times[(job_id, op_idx)] = op_times
                twk += min_time # Tính TWK dựa trên thời gian thực thi ngắn nhất
                
            self.total_work_content[job_id] = twk
            
            # Tính due date: Nếu user chỉ định thì dùng, không thì tự tính
            if 'due_date' in job:
                # Đổi due_date (datetime object) thành số phút tương đối so với t=0
                # Giả sử t=0 là bây giờ
                import datetime
                base_time = datetime.datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
                diff = job['due_date'] - base_time
                self.job_due_dates[job_id] = int(diff.total_seconds() / 60)
            else:
                self.job_due_dates[job_id] = int(twk * self.tightness_factor)
                
            # Lưu priority weight
            if job.get('priority') == 'Gấp':
                self.job_priority_weight[job_id] = 10.0
            elif job.get('priority') == 'Cao':
                self.job_priority_weight[job_id] = 3.0
            else:
                self.job_priority_weight[job_id] = 1.0

    def get_setup_time(self, m_id, prev_job_id, curr_job_id):
        # Mô phỏng Sequence-Dependent Setup Time.
        # Nếu có setup_matrix trong máy thì dùng, nếu không thì trả về setup mặc định.
        if prev_job_id is None or prev_job_id == curr_job_id:
            return 5
        machine_info = self.machines_data.get(m_id, {})
        setup_matrix = machine_info.get("setup_matrix", {})
        if prev_job_id in setup_matrix and curr_job_id in setup_matrix[prev_job_id]:
            return setup_matrix[prev_job_id][curr_job_id]
        
        # Sequence ngẫu nhiên giả lập nếu ko có (trong thực tế lấy từ data)
        # Setup = 5 phút nếu đổi job
        return 10

    # --- INITIALIZATION STRATEGIES ---
    
    def random_machine_selection(self):
        ms = {}
        for (job_id, op_idx), m_times in self.processing_times.items():
            ms[(job_id, op_idx)] = random.choice(list(m_times.keys()))
        return ms

    def spt_machine_selection(self):
        # Shortest Processing Time
        ms = {}
        for (job_id, op_idx), m_times in self.processing_times.items():
            best_m = min(m_times, key=m_times.get)
            ms[(job_id, op_idx)] = best_m
        return ms

    def random_operation_sequence(self):
        os = [job_id for _, _, job_id in self.job_ops]
        random.shuffle(os)
        return os

    def lwkr_fdd_operation_sequence(self):
        # Least Work Remaining + Flow Due Date
        # Đơn giản hoá bằng cách random mix nhưng ưu tiên job có (Due Date - TWK) nhỏ
        # Sắp xếp các job theo (Due Date - TWK)
        prioritized_jobs = sorted(self.jobs, key=lambda j: self.job_due_dates[j['id']] - self.total_work_content[j['id']])
        job_ids = [j['id'] for j in prioritized_jobs]
        
        # Mở phẳng danh sách job_ID theo số phép toán
        os = []
        for j_id in job_ids:
            num_ops = len(self.job_dict[j_id].get('operations', []))
            os.extend([j_id] * num_ops)
            
        # Add random noise để không cứng nhắc
        # Chọn ra 10% để swap
        n_swaps = int(len(os) * 0.1)
        for _ in range(n_swaps):
            i, j = random.sample(range(len(os)), 2)
            os[i], os[j] = os[j], os[i]
        return os

    def cr_operation_sequence(self):
        # Critical Ratio: (Due Date - current time) / Work Remaining
        # Ở lúc t=0, tương tự FDD, sắp xếp theo Due Date / TWK
        prioritized_jobs = sorted(self.jobs, key=lambda j: self.job_due_dates[j['id']] / max(1, self.total_work_content[j['id']]))
        os = []
        for j in prioritized_jobs:
            num_ops = len(j.get('operations', []))
            os.extend([j['id']] * num_ops)
        return os

    def initialize_population(self):
        population = []
        sub_size = self.pop_size // 4
        
        # P1: Random MS, Random OS
        for _ in range(sub_size):
            population.append({'MS': self.random_machine_selection(), 'OS': self.random_operation_sequence()})
            
        # P2: SPT MS, Random OS
        for _ in range(sub_size):
            population.append({'MS': self.spt_machine_selection(), 'OS': self.random_operation_sequence()})
            
        # P3: Random MS, LWKR + FDD OS
        for _ in range(sub_size):
            population.append({'MS': self.random_machine_selection(), 'OS': self.lwkr_fdd_operation_sequence()})
            
        # P4: Random MS, CR OS
        for _ in range(self.pop_size - len(population)):
            population.append({'MS': self.random_machine_selection(), 'OS': self.cr_operation_sequence()})
            
        return population

    # --- FITNESS EUVALUATION ---
    def decode_and_evaluate(self, individual):
        ms = individual['MS']
        os = individual['OS']
        
        machine_avail = defaultdict(int)
        machine_last_job = defaultdict(lambda: None)
        job_avail = defaultdict(int)
        
        op_counts = defaultdict(int)
        
        makespan = 0
        total_setup_time = 0
        
        schedule = []
        
        for job_id in os:
            op_idx = op_counts[job_id]
            op_counts[job_id] += 1
            
            m_id = ms[(job_id, op_idx)]
            dur = self.processing_times[(job_id, op_idx)][m_id]
            
            prev_job_id = machine_last_job[m_id]
            setup = self.get_setup_time(m_id, prev_job_id, job_id)
            
            start_time = max(machine_avail[m_id], job_avail[job_id])
            
            # Cân nhắc setup time vào lịch trình
            if machine_avail[m_id] <= job_avail[job_id]:
                # Máy rảnh trước job, xử lý setup
                actual_start = max(job_avail[job_id], machine_avail[m_id] + setup)
            else:
                # Job rảnh trước máy, máy phải setup xong
                actual_start = machine_avail[m_id] + setup
                
            finish_time = actual_start + dur
            
            total_setup_time += setup
            machine_avail[m_id] = finish_time
            job_avail[job_id] = finish_time
            machine_last_job[m_id] = job_id
            
            makespan = max(makespan, finish_time)
            
            schedule.append({
                "job_id": job_id,
                "op_idx": op_idx,
                "machine": m_id,
                "start": actual_start,
                "finish": finish_time,
                "setup": setup
            })
            
        # Tính Tardiness
        total_tardiness = 0
        for job_id, completion_time in job_avail.items():
            due_date = self.job_due_dates[job_id]
            tardy = max(0, completion_time - due_date)
            # Nhân với trọng số ưu tiên để ép Job quan trọng không bị trễ
            weighted_tardy = tardy * self.job_priority_weight.get(job_id, 1.0)
            total_tardiness += weighted_tardy
            
        # Multi-objective Fitness (Equal weights)
        fitness = (makespan + total_setup_time + total_tardiness) / 3.0
        
        return fitness, makespan, total_setup_time, total_tardiness, schedule

    # --- GA OPERATORS ---
    def crossover_os(self, os1, os2):
        # Dùng Precedence Preserving Order-Based Crossover (POX)
        jobs_set = list(self.job_dict.keys())
        p_len = len(jobs_set)
        num_transfer = random.randint(1, max(1, p_len // 2))
        selected_jobs = set(random.sample(jobs_set, num_transfer))
        
        child1 = [-1] * len(os1)
        child2 = [-1] * len(os2)
        
        # Copy selected jobs
        for i, val in enumerate(os1):
            if val in selected_jobs: child1[i] = val
        for i, val in enumerate(os2):
            if val in selected_jobs: child2[i] = val
            
        # Fill remaining
        idx = 0
        for i in range(len(child1)):
            if child1[i] == -1:
                while os2[idx] in selected_jobs:
                    idx += 1
                child1[i] = os2[idx]
                idx += 1
                
        idx = 0
        for i in range(len(child2)):
            if child2[i] == -1:
                while os1[idx] in selected_jobs:
                    idx += 1
                child2[i] = os1[idx]
                idx += 1
                
        return child1, child2

    def crossover_ms(self, ms1, ms2):
        child1, child2 = {}, {}
        for k in ms1.keys():
            if random.random() < 0.5:
                child1[k], child2[k] = ms1[k], ms2[k]
            else:
                child1[k], child2[k] = ms2[k], ms1[k]
        return child1, child2

    # --- VNS LOCAL SEARCH ---
    def vns_local_search(self, individual):
        # Nếu tổng số nguyên công (tổng chiều dài chuỗi OS) nhỏ hơn 2,
        # không thể hoán đổi thư tự, bỏ qua VNS
        if len(individual['OS']) < 2:
            return individual
            
        best_ind = copy.deepcopy(individual)
        best_fit, _, _, _, _ = self.decode_and_evaluate(best_ind)
        
        # 4 Cấu trúc lân cận N1 -> N4
        # Áp dụng lên mảng OS
        improved = True
        max_vns_iter = 5
        curr_iter = 0
        
        while curr_iter < max_vns_iter and improved:
            curr_iter += 1
            improved = False
            
            # Neighborhoods: N1, N2, N3, N4
            for n_type in range(1, 5):
                candidate = copy.deepcopy(best_ind)
                os = candidate['OS']
                n_len = len(os)
                
                if n_type == 1:
                    # N1: Swap
                    i, j = random.sample(range(n_len), 2)
                    os[i], os[j] = os[j], os[i]
                elif n_type == 2:
                    # N2: Reversion
                    i, j = sorted(random.sample(range(n_len), 2))
                    os[i:j+1] = reversed(os[i:j+1])
                elif n_type == 3:
                    # N3: Insertion
                    i, j = random.sample(range(n_len), 2)
                    job = os.pop(i)
                    if j > i: j -= 1
                    os.insert(j, job)
                elif n_type == 4:
                    # N4: Rearrangement (Shuffle 4 spots)
                    if n_len > 4:
                        indices = random.sample(range(n_len), 4)
                        vals = [os[i] for i in indices]
                        random.shuffle(vals)
                        for idx, v in zip(indices, vals):
                            os[idx] = v
                
                # Check valid (OS always valid if counting maintains)
                cand_fit, _, _, _, _ = self.decode_and_evaluate(candidate)
                if cand_fit < best_fit:
                    best_ind = candidate
                    best_fit = cand_fit
                    improved = True
                    break # Restart with new best
                    
        return best_ind

    def solve(self):
        pop = self.initialize_population()
        
        best_overall = None
        best_fitness = float('inf')
        
        # We need to explicitly track the best individual for our 3 criteria.
        best_balanced_ind = None
        best_balanced_fit = float('inf')
        
        best_makespan_ind = None
        best_makespan_val = float('inf')
        
        best_setup_ind = None
        best_setup_val = float('inf')
        
        # Start Evolution
        for gen in range(self.max_gen):
            scored_pop = []
            for ind in pop:
                fit, mk, tst, tardy, sched = self.decode_and_evaluate(ind)
                scored_pop.append((fit, ind, mk, tst, tardy, sched))
                
                # Balanced (best fitness)
                if fit < best_balanced_fit:
                    best_balanced_fit = fit
                    best_balanced_ind = (fit, ind, mk, tst, tardy, sched)
                    
                # Makespan Optimized (Speed)
                if mk < best_makespan_val or (mk == best_makespan_val and fit < (best_makespan_ind[0] if best_makespan_ind else float('inf'))):
                    best_makespan_val = mk
                    best_makespan_ind = (fit, ind, mk, tst, tardy, sched)
                    
                # Setup Optimized (Cost)
                if tst < best_setup_val or (tst == best_setup_val and fit < (best_setup_ind[0] if best_setup_ind else float('inf'))):
                    best_setup_val = tst
                    best_setup_ind = (fit, ind, mk, tst, tardy, sched)
                    
            # Selection (Tournament)
            scored_pop.sort(key=lambda x: x[0])
            new_pop = [x[1] for x in scored_pop[:2]] # Elitism giữ 2 cá thể tốt nhất
            
            while len(new_pop) < self.pop_size:
                # Random selection từ top 50%
                p1 = random.choice(scored_pop[:self.pop_size//2])[1]
                p2 = random.choice(scored_pop[:self.pop_size//2])[1]
                
                # Crossover
                if random.random() < 0.8:
                    c1_os, c2_os = self.crossover_os(p1['OS'], p2['OS'])
                    c1_ms, c2_ms = self.crossover_ms(p1['MS'], p2['MS'])
                    c1 = {'MS': c1_ms, 'OS': c1_os}
                    c2 = {'MS': c2_ms, 'OS': c2_os}
                else:
                    c1, c2 = copy.deepcopy(p1), copy.deepcopy(p2)
                    
                # Mutation (có thể được cover bởi VNS, nhưng thêm 1 chút đột biến cơ bản)
                if random.random() < 0.1:
                    k = random.choice(list(c1['MS'].keys()))
                    c1['MS'][k] = random.choice(list(self.processing_times[k].keys()))
                    
                # VNS Local search on children (xác suất 10% để giảm thời gian gian chạy)
                if random.random() < 0.1:
                    c1 = self.vns_local_search(c1)
                    
                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)
                    
            pop = new_pop
            
        # Collect distinct options
        options = []
        seen_schedules = set()
        
        def add_option(name, ind_tuple):
            if not ind_tuple: return
            fit, ind, mk, tst, tardy, sched = ind_tuple
            
            # Create a simple hash/string of the schedule to verify uniqueness
            sched_hash = "".join([f"{s['job_id']}_{s['machine']}_{s['start']}" for s in sched])
            if sched_hash not in seen_schedules:
                seen_schedules.add(sched_hash)
                options.append({
                    "name": name,
                    "schedule": sched,
                    "metrics": {
                        "fitness": round(fit, 2),
                        "makespan": mk,
                        "setup": tst,
                        "tardiness": tardy
                    }
                })

        # Add the options in order of preference
        add_option("Phương án Cân bằng (Balanced)", best_balanced_ind)
        add_option("Phương án Nhanh nhất (Speed/Makespan)", best_makespan_ind)
        add_option("Phương án Tối ưu Gá đặt (Cost/Setup)", best_setup_ind)
        
        # Fill up to 3 options if we didn't find enough unique ones
        idx = 0
        while len(options) < 3 and idx < len(scored_pop):
            # scored_pop is sorted by fitness
            add_option(f"Phương án Phụ (Thay thế {len(options)+1})", scored_pop[idx])
            idx += 1
            
        print(f"GA-VNS Completed. Generated {len(options)} options.")
        for i, opt in enumerate(options):
            m = opt['metrics']
            print(f" Opt {i+1}: {opt['name']} | Fit: {m['fitness']} | Mk: {m['makespan']} | Setup: {m['setup']} | Tardy: {m['tardiness']}")
            
        return options

