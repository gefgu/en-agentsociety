from en_agentsociety.simulation import AgentSociety
from en_agentsociety.configs import IndividualConfig

async def entry(config: IndividualConfig, tenant_id: str):
    # ========================    
    # create agentsociety
    # ========================
    agentsociety = AgentSociety.create(config, tenant_id)
    # ========================    
    # init agentsociety
    # ========================
    await en_agentsociety.init()
    # ========================    
    # run agentsociety
    # ========================
    await en_agentsociety.run()
    # ========================    
    # get results
    # ========================
    assert en_agentsociety._database_writer is not None
    results = await en_agentsociety._database_writer.read_task_results()
    # ========================    
    # close agentsociety
    # ========================
    await en_agentsociety.close()
    return results