service AgentService {
    string version(),
    string run_command(1:string command, 2:bool sync),
    oneway void run_command_async(1: string command),
    string run_script(1:string name, 2:string content, 3:string checksum, 4:string main_func, 5:string json_args, 6:bool sync),
    oneway void run_script_async(1:string name, 2:string content, 3:string checksum, 4:string main_func, 5:string json_args),
    oneway void scheduler_run_script(1:string cr_event, 2:string machine_id, 3:string name, 4:string content, 5:string checksum, 6:string main_func, 7:string script_args, 8:string trigger_args, 9:string report_url),
    string scheduler_job_action(1:string cr_event, 2:string machine_id, 3:string action)
}