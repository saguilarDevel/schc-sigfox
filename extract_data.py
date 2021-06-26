import json
import matplotlib.pyplot as plt
from mpl_toolkits.axisartist import SubplotZero

json_file = "results2.json"

with open(json_file, 'r') as f:
    json_dict = json.load(f)

loss_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
success = [None] * len(loss_rates)
failed_reassembly = [None] * len(loss_rates)
sender_aborted = [None] * len(loss_rates)
receiver_aborted = [None] * len(loss_rates)

for loss_rate in json_dict.keys():
    success_count = 0
    fail_count = 0
    s_abort_count = 0
    r_abort_count = 0
    for repetition in json_dict[loss_rate].keys():

        if json_dict[loss_rate][repetition]["sender_abort"]:
            s_abort_count += 1

        if json_dict[loss_rate][repetition]["receiver_abort"]:
            r_abort_count += 1

        aborted = json_dict[loss_rate][repetition]["sender_abort"] or json_dict[loss_rate][repetition]["receiver_abort"]

        if not aborted and not json_dict[loss_rate][repetition]["reassemble_success"]:
            fail_count += 1

        if not aborted and json_dict[loss_rate][repetition]["reassemble_success"]:
            success_count += 1

    i = loss_rates.index(int(loss_rate))

    success[i] = success_count
    failed_reassembly[i] = fail_count
    sender_aborted[i] = s_abort_count
    receiver_aborted[i] = r_abort_count

print(f"Success:\n{success}")
print(f"Failed reassembly:\n{failed_reassembly}")
print(f"Sender aborted:\n{sender_aborted}")
print(f"Receiver aborted:\n{receiver_aborted}")

fig = plt.figure()
ax = SubplotZero(fig, 111)
fig.add_subplot(ax)
ax.grid(True, ls='dotted')
x_axis = [l / 100 for l in loss_rates]
ax.plot(x_axis, [x / 100 for x in sender_aborted])
ax.plot(x_axis, [x / 100 for x in receiver_aborted])
ax.plot(x_axis, [x / 100 for x in failed_reassembly], color='r', linewidth=4)
ax.set_xlabel("Fragment loss rate")
ax.set_ylabel("Occurrences / Total experiments")
ax.set_xlim((0, 1))
ax.set_ylim((0, 1))
plt.legend(["Sender-Aborted", "Receiver-Aborted", "Failed reassembly"])
plt.show()
fig.savefig("failed_total.png")

fail_rate = [None] * len(loss_rates)
completion_rate = [None] * len(loss_rates)
for i in range(len(loss_rates)):
    try:
        fail_rate[i] = failed_reassembly[i] / (success[i] + failed_reassembly[i])
        completion_rate[i] = (success[i] + failed_reassembly[i]) / 100
    except ZeroDivisionError:
        fail_rate[i] = None

fig = plt.figure()
ax = SubplotZero(fig, 111)
fig.add_subplot(ax)
ax.grid(True, ls='dotted')
ax.plot(x_axis, fail_rate, color='r', linewidth=4)
# ax.plot(x_axis, completion_rate)
ax.set_xlabel("Fragment loss rate")
ax.set_ylabel("Occurrences / (Correct + Failed)")
ax.set_xlim((0, 1))
ax.set_ylim((0, 1))
plt.legend(["Failed reassembly"])
plt.show()
fig.savefig("failed_rate.png")
