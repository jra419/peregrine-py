#pragma once

#include "table.h"

#include <map>

namespace peregrine {

class Port_HDL_Info : Table {
private:
  // Key fields IDs
  bf_rt_id_t CONN_ID;
  bf_rt_id_t CHNL_ID;

  // Data field ids
  bf_rt_id_t DEV_PORT;

public:
  Port_HDL_Info(const bfrt::BfRtInfo *bfrt_info,
                std::shared_ptr<bfrt::BfRtSession> bfrt_session,
                const bf_rt_target_t &dev_tgt)
      : Table(bfrt_info, bfrt_session, dev_tgt, "$PORT_HDL_INFO") {
    auto bf_status = table->keyFieldIdGet("$CONN_ID", &CONN_ID);
    assert(bf_status == BF_SUCCESS);
    bf_status = table->keyFieldIdGet("$CHNL_ID", &CHNL_ID);
    assert(bf_status == BF_SUCCESS);

    bf_status = table->dataFieldIdGet("$DEV_PORT", &DEV_PORT);
    assert(bf_status == BF_SUCCESS);
  }

  uint16_t get_dev_port(uint16_t front_panel_port, uint16_t lane,
                        bool from_hw = false) {
    auto hwflag = from_hw ? bfrt::BfRtTable::BfRtTableGetFlag::GET_FROM_HW
                          : bfrt::BfRtTable::BfRtTableGetFlag::GET_FROM_SW;

    key_setup(front_panel_port, lane);
    auto bf_status =
        table->tableEntryGet(*session, dev_tgt, *key, hwflag, data.get());
    assert(bf_status == BF_SUCCESS);

    uint64_t value;
    bf_status = data->getValue(DEV_PORT, &value);
    assert(bf_status == BF_SUCCESS);

    return (uint16_t)value;
  }

private:
  void key_setup(uint16_t front_panel_port, uint16_t lane) {
    table->keyReset(key.get());

    auto bf_status =
        key->setValue(CONN_ID, static_cast<uint64_t>(front_panel_port));
    assert(bf_status == BF_SUCCESS);

    bf_status = key->setValue(CHNL_ID, static_cast<uint64_t>(lane));
    assert(bf_status == BF_SUCCESS);
  }
};

class Ports : Table {
private:
  // Key fields IDs
  bf_rt_id_t DEV_PORT;

  // Data field ids
  bf_rt_id_t SPEED;
  bf_rt_id_t FEC;
  bf_rt_id_t PORT_ENABLE;

  Port_HDL_Info port_hdl_info;

public:
  Ports(const bfrt::BfRtInfo *bfrt_info,
        std::shared_ptr<bfrt::BfRtSession> session,
        const bf_rt_target_t &dev_tgt)
      : Table(bfrt_info, session, dev_tgt, "$PORT"),
        port_hdl_info(bfrt_info, session, dev_tgt) {
    auto bf_status = table->keyFieldIdGet("$DEV_PORT", &DEV_PORT);
    assert(bf_status == BF_SUCCESS);

    bf_status = table->dataFieldIdGet("$SPEED", &SPEED);
    assert(bf_status == BF_SUCCESS);
    bf_status = table->dataFieldIdGet("$FEC", &FEC);
    assert(bf_status == BF_SUCCESS);
    bf_status = table->dataFieldIdGet("$PORT_ENABLE", &PORT_ENABLE);
    assert(bf_status == BF_SUCCESS);
  }

  void add_port(uint16_t front_panel_port, uint16_t lane,
                bf_port_speed_t speed) {
    std::map<bf_port_speed_t, std::string> speed_opts{
        {BF_SPEED_NONE, "BF_SPEED_10G"},
        {BF_SPEED_25G, "BF_SPEED_25G"},
        {BF_SPEED_40G, "BF_SPEED_40G"},
        {BF_SPEED_50G, "BF_SPEED_50G"},
        {BF_SPEED_100G, "BF_SPEED_100G"}};

    std::map<bf_fec_type_t, std::string> fec_opts{
        {BF_FEC_TYP_NONE, "BF_FEC_TYP_NONE"},
        {BF_FEC_TYP_FIRECODE, "BF_FEC_TYP_FIRECODE"},
        {BF_FEC_TYP_REED_SOLOMON, "BF_FEC_TYP_REED_SOLOMON"}};

    std::map<bf_port_speed_t, bf_fec_type_t> speed_to_fec{
        {BF_SPEED_NONE, BF_FEC_TYP_NONE},
        {BF_SPEED_25G, BF_FEC_TYP_NONE},
        {BF_SPEED_40G, BF_FEC_TYP_NONE},
        {BF_SPEED_50G, BF_FEC_TYP_NONE},
        {BF_SPEED_50G, BF_FEC_TYP_NONE},
        {BF_SPEED_100G, BF_FEC_TYP_REED_SOLOMON},
    };

    auto fec = speed_to_fec[speed];
    auto dev_port = port_hdl_info.get_dev_port(front_panel_port, lane);

    key_setup(dev_port);
    data_setup(speed_opts[speed], fec_opts[fec], true);

    auto bf_status = table->tableEntryAdd(*session, dev_tgt, *key, *data);
    assert(bf_status == BF_SUCCESS);
  }

private:
  void key_setup(uint16_t dev_port) {
    table->keyReset(key.get());

    auto bf_status = key->setValue(DEV_PORT, static_cast<uint64_t>(dev_port));
    assert(bf_status == BF_SUCCESS);
  }

  void data_setup(std::string speed, std::string fec, bool port_enable) {
    table->dataReset(data.get());

    auto bf_status = data->setValue(SPEED, speed);
    assert(bf_status == BF_SUCCESS);
    bf_status = data->setValue(FEC, fec);
    assert(bf_status == BF_SUCCESS);
    bf_status = data->setValue(PORT_ENABLE, port_enable);
    assert(bf_status == BF_SUCCESS);
  }
};

}; // namespace nat